"""
Serviço de processamento e anonimização de PDFs
"""
import re
import hashlib
import unicodedata
from typing import Dict, List, Tuple, Set
from pypdf import PdfReader, PdfWriter
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from django.core.files.base import ContentFile
from apps.terms.models import Term, IgnoredTerm


class PDFProcessor:
    """Processa e anonimiza PDFs de notas técnicas"""
    
    @staticmethod
    def extract_note_info(text: str) -> Dict[str, any]:
        """
        Extrai informações da nota técnica do texto
        
        Args:
            text: Texto extraído do PDF
            
        Returns:
            Dict com 'name' e 'year' da nota
        """
        info = {'name': None, 'year': None}
        
        # Padrões para identificar nota técnica completa
        # Captura o nome completo incluindo códigos (DILAG, COLEMP, etc)
        patterns = [
            # Padrão: NOTA TÉCNICA N.º 95/2025/DILAG/COLEMP/CGGP/DGP-INSS (mais específico primeiro)
            r'(NOTA\s+T[ÉE]CNICA\s+N\.?[ºO°]?\s*\d+/\d{4}(?:/[\w\-]+)+)',
            # Padrão: NOTA TÉCNICA Nº 95/2025
            r'(NOTA\s+T[ÉE]CNICA\s+N\.?[ºO°]?\s*\d+/\d{4})',
            # Padrão: NT N. 95/2025
            r'(NT\s+N\.?[ºO°]?\s*\d+/\d{4})',
            # Padrão: PARECER TÉCNICO Nº 95/2025
            r'(PARECER\s+T[ÉE]CNICO\s+N\.?[ºO°]?\s*\d+/\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                nota_completa = match.group(1)
                # Limpa espaços extras
                info['name'] = re.sub(r'\s+', ' ', nota_completa).strip()
                
                # Extrai ano se presente
                year_match = re.search(r'/(\d{4})(?:/|$)', nota_completa)
                if year_match:
                    info['year'] = int(year_match.group(1))
                break
        
        # Se não encontrou, usa título genérico
        if not info['name']:
            info['name'] = "Nota Técnica (sem identificação)"
        
        # Busca ano separadamente se não encontrado
        if not info['year']:
            year_patterns = [
                r'\b(20\d{2})\b',  # Anos 2000-2099
                r'(\d{2})/(\d{2})/(\d{4})',  # Datas dd/mm/yyyy
            ]
            
            for pattern in year_patterns:
                match = re.search(pattern, text[:2000])  # Busca nos primeiros 2000 chars
                if match:
                    year_str = match.group(1) if len(match.groups()) == 1 else match.group(3)
                    year = int(year_str)
                    if 2000 <= year <= 2100:
                        info['year'] = year
                        break
        
        return info
    
    @staticmethod
    def calculate_hash(file_content: bytes) -> str:
        """Calcula hash SHA-256 do arquivo"""
        return hashlib.sha256(file_content).hexdigest()
    
    @staticmethod
    def extract_text(pdf_file) -> str:
        """
        Extrai todo o texto do PDF
        
        Args:
            pdf_file: Arquivo PDF (file-like object)
            
        Returns:
            Texto completo do PDF
        """
        try:
            reader = PdfReader(pdf_file)
            text_parts = []
            
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            return '\n'.join(text_parts)
        except Exception as e:
            raise ValueError(f"Erro ao extrair texto do PDF: {str(e)}")
    
    @staticmethod
    def normalize_for_search(text: str) -> str:
        """
        Normaliza texto removendo acentos para busca
        """
        # Remove acentos
        nfkd = unicodedata.normalize('NFKD', text)
        return ''.join([c for c in nfkd if not unicodedata.combining(c)])
    
    @staticmethod
    def create_accent_insensitive_pattern(term: str) -> re.Pattern:
        """
        Cria padrão regex que ignora acentos
        Normaliza o termo primeiro e depois cria padrão que aceita qualquer variação
        """
        # Normaliza o termo (remove acentos)
        normalized = PDFProcessor.normalize_for_search(term)
        
        # Mapa de substituições - cada caractere sem acento aceita versões com acento
        accent_map = {
            'a': '[aáàâãäåAÁÀÂÃÄÅ]',
            'e': '[eéèêëEÉÈÊË]',
            'i': '[iíìîïIÍÌÎÏ]',
            'o': '[oóòôõöOÓÒÔÕÖ]',
            'u': '[uúùûüUÚÙÛÜ]',
            'c': '[cçCÇ]',
            'n': '[nñNÑ]',
        }
        
        # Cria padrão a partir do termo normalizado
        pattern = ''
        for char in normalized:
            lower_char = char.lower()
            if lower_char in accent_map:
                pattern += accent_map[lower_char]
            elif char.isalpha():
                # Letras sem acento: aceita maiúscula e minúscula
                pattern += f'[{char.lower()}{char.upper()}]'
            else:
                # Outros caracteres (espaços, hífens, etc): escapar
                pattern += re.escape(char)
        
        return re.compile(pattern)
    
    @staticmethod
    def find_sensitive_terms(text: str) -> List[Tuple[str, str, str]]:
        """
        Identifica termos sensíveis no texto, excluindo termos ignorados
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            Lista de tuplas (termo, termo_normalizado, categoria)
        """
        found_terms = []
        text_normalized = Term.normalize_text(text)
        
        # Carrega termos ignorados (whitelist)
        ignored_set = IgnoredTerm.get_ignored_set()
        
        # Padrões de contexto para SIAPE/matrícula
        siape_context_pattern = re.compile(
            r'(?:SIAPE|matr[íi]cula|servidor(?:\(a\))?|identifica[çc][ãa]o|registro|n[úu]mero\s+(?:de\s+)?(?:SIAPE|matr[íi]cula))'
            r'[\s\W]{0,50}?',
            re.IGNORECASE
        )
        
        # Cache de termos já encontrados (evita duplicatas)
        found_set = set()
        
        # Busca termos por categoria
        for category in ['siape', 'nome', 'cpf']:
            terms = Term.objects.filter(
                category=category,
                enabled=True
            ).values_list('term', 'norm_term')
            
            for term, norm_term in terms:
                # Pula se já encontrado ou estiver na whitelist
                if norm_term in found_set or norm_term in ignored_set:
                    continue
                
                # Verifica se termo normalizado existe no texto normalizado (filtro rápido)
                if norm_term not in text_normalized:
                    continue
                
                # Para SIAPE: verifica contexto específico
                if category == 'siape':
                    pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
                    matches = pattern.finditer(text)
                    
                    for match in matches:
                        start = max(0, match.start() - 50)
                        context_before = text[start:match.start()]
                        
                        if siape_context_pattern.search(context_before):
                            found_terms.append((term, norm_term, category))
                            found_set.add(norm_term)
                            break
                
                # Para nomes: busca com padrão que ignora acentos
                # Se nome tem mais de 2 palavras, também busca palavras individuais
                elif category == 'nome':
                    pattern = PDFProcessor.create_accent_insensitive_pattern(term)
                    if pattern.search(text):
                        found_terms.append((term, norm_term, category))
                        found_set.add(norm_term)
                    else:
                        # Se não encontrou o nome completo e tem múltiplas palavras,
                        # busca cada parte com mais de 3 caracteres (evita iniciais)
                        words = term.split()
                        if len(words) > 1:
                            for word in words:
                                if len(word) > 3:  # Ignora iniciais e palavras muito curtas
                                    word_norm = Term.normalize_text(word)
                                    if word_norm not in found_set and word_norm in text_normalized:
                                        word_pattern = PDFProcessor.create_accent_insensitive_pattern(word)
                                        if word_pattern.search(text):
                                            found_terms.append((word, word_norm, category))
                                            found_set.add(word_norm)
                
                # Para CPFs: busca com padrão que ignora acentos
                elif category == 'cpf':
                    pattern = PDFProcessor.create_accent_insensitive_pattern(term)
                    if pattern.search(text):
                        found_terms.append((term, norm_term, category))
                        found_set.add(norm_term)
        
        return found_terms
    
    @staticmethod
    def anonymize_text(text: str, terms: List[Tuple[str, str, str]]) -> str:
        """
        Remove termos sensíveis do texto
        
        Args:
            text: Texto original
            terms: Lista de tuplas (termo, termo_normalizado, categoria)
            
        Returns:
            Texto anonimizado
        """
        anonymized = text
        
        # Agrupa termos por categoria para substituição eficiente
        replacements = {
            'siape': '[SIAPE ANONIMIZADO]',
            'nome': '[NOME ANONIMIZADO]',
            'cpf': '[CPF ANONIMIZADO]',
        }
        
        # Remove duplicatas e ordena por tamanho (maior primeiro)
        unique_terms = list(set(terms))
        unique_terms.sort(key=lambda x: len(x[0]), reverse=True)
        
        for term, norm_term, category in unique_terms:
            replacement = replacements.get(category, '[DADO ANONIMIZADO]')
            
            # Para nomes e CPFs: usa padrão que ignora acentos
            if category in ['nome', 'cpf']:
                pattern = PDFProcessor.create_accent_insensitive_pattern(term)
            else:
                # Para SIAPE: busca exata com case-insensitive
                pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            
            anonymized = pattern.sub(replacement, anonymized)
        
        return anonymized
    
    @classmethod
    def process_pdf(cls, pdf_file, filename: str) -> Dict:
        """
        Processa PDF completo: extração, detecção e anonimização
        
        Args:
            pdf_file: Arquivo PDF
            filename: Nome do arquivo
            
        Returns:
            Dict com informações processadas:
            {
                'hash': hash SHA-256,
                'original_text': texto original,
                'anonymized_text': texto anonimizado,
                'note_name': nome da nota,
                'year': ano,
                'sensitive_terms': lista de termos encontrados,
                'anonymized_pdf': arquivo PDF anonimizado (bytes)
            }
        """
        # Lê conteúdo do arquivo
        pdf_file.seek(0)
        file_content = pdf_file.read()
        pdf_file.seek(0)
        
        # Calcula hash
        file_hash = cls.calculate_hash(file_content)
        
        # Extrai texto
        original_text = cls.extract_text(pdf_file)
        
        # Extrai informações da nota
        note_info = cls.extract_note_info(original_text)
        
        # Identifica termos sensíveis
        sensitive_terms = cls.find_sensitive_terms(original_text)
        
        # Anonimiza texto
        anonymized_text = cls.anonymize_text(original_text, sensitive_terms)
        
        # Cria PDF anonimizado
        pdf_file.seek(0)
        anonymized_pdf_content = cls.create_anonymized_pdf(
            pdf_file, 
            sensitive_terms
        )
        
        return {
            'hash': file_hash,
            'original_text': original_text,
            'anonymized_text': anonymized_text,
            'note_name': note_info['name'],
            'year': note_info['year'],
            'sensitive_terms': sensitive_terms,
            'anonymized_pdf': anonymized_pdf_content,
        }
    
    @staticmethod
    def generate_accent_variations(text: str) -> set:
        """
        Gera variações de um texto com diferentes acentuações
        Para cada vogal sem acento, gera versões com acentos comuns
        """
        # Mapa de caracteres -> suas variações com acento
        accent_variations = {
            'a': ['a', 'á', 'à', 'â', 'ã', 'ä'],
            'e': ['e', 'é', 'è', 'ê', 'ë'],
            'i': ['i', 'í', 'ì', 'î', 'ï'],
            'o': ['o', 'ó', 'ò', 'ô', 'õ', 'ö'],
            'u': ['u', 'ú', 'ù', 'û', 'ü'],
            'c': ['c', 'ç'],
            'n': ['n', 'ñ'],
            'A': ['A', 'Á', 'À', 'Â', 'Ã', 'Ä'],
            'E': ['E', 'É', 'È', 'Ê', 'Ë'],
            'I': ['I', 'Í', 'Ì', 'Î', 'Ï'],
            'O': ['O', 'Ó', 'Ò', 'Ô', 'Õ', 'Ö'],
            'U': ['U', 'Ú', 'Ù', 'Û', 'Ü'],
            'C': ['C', 'Ç'],
            'N': ['N', 'Ñ'],
        }
        
        def generate_variations_recursive(s: str, index: int) -> set:
            if index >= len(s):
                return {s}
            
            char = s[index]
            rest_variations = generate_variations_recursive(s, index + 1)
            
            if char in accent_variations:
                result = set()
                for variation in accent_variations[char]:
                    for rest in rest_variations:
                        result.add(s[:index] + variation + rest[index+1:])
                return result
            else:
                return rest_variations
        
        # Limita o tamanho para evitar explosão combinatória
        # Se o texto for muito grande, gera apenas variações básicas
        if len(text) > 20:
            variations = {text}
            # Gera apenas algumas variações comuns para textos longos
            normalized = PDFProcessor.normalize_for_search(text)
            if normalized != text:
                variations.add(normalized)
            # Variações de case
            variations.add(text.upper())
            variations.add(text.lower())
            variations.add(text.capitalize())
            variations.add(text.title())
            return variations
        
        # Para textos curtos, gera mais variações (mas limita a 100)
        variations = generate_variations_recursive(text, 0)
        return set(list(variations)[:100])  # Limita a 100 variações
    
    @staticmethod
    def create_anonymized_pdf(pdf_file, terms: List[Tuple[str, str, str]]) -> bytes:
        """
        Cria versão anonimizada do PDF usando PyMuPDF (fitz)
        
        Esta função busca e redact (remove) termos sensíveis do PDF,
        substituindo-os por texto de placeholder com fundo preto.
        
        Args:
            pdf_file: Arquivo PDF original
            terms: Lista de termos a anonimizar (termo, norm_term, categoria)
            
        Returns:
            Bytes do PDF anonimizado
        """
        try:
            # Lê conteúdo do PDF
            pdf_file.seek(0)
            pdf_bytes = pdf_file.read()
            
            # Abre documento com PyMuPDF
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # Agrupa substituições
            replacements = {
                'siape': '[SIAPE]',
                'nome': '[NOME]',
                'cpf': '[CPF]',
            }
            
            # Remove duplicatas e agrupa por categoria
            terms_by_category = {}
            for term, norm_term, category in terms:
                if category not in terms_by_category:
                    terms_by_category[category] = []
                terms_by_category[category].append(term)
            
            # Processa cada página
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Para cada categoria de termo
                for category, term_list in terms_by_category.items():
                    replacement = replacements.get(category, '[REMOVIDO]')
                    
                    # Para cada termo na categoria
                    for term in term_list:
                        # Para nomes e CPFs: gera variações completas de acentos
                        if category in ['nome', 'cpf']:
                            variations = PDFProcessor.generate_accent_variations(term)
                        else:
                            # Para SIAPE: apenas variações de case
                            variations = {
                                term,
                                term.upper(),
                                term.lower(),
                                term.capitalize(),
                                term.title()
                            }
                        
                        # Busca todas as variações
                        text_instances = []
                        for variation in variations:
                            found = page.search_for(variation, flags=fitz.TEXT_PRESERVE_WHITESPACE)
                            text_instances.extend(found)
                        
                        # Redact (remove) cada ocorrência
                        for inst in text_instances:
                            # Adiciona anotação de redação
                            page.add_redact_annot(
                                inst,
                                text=replacement,
                                fill=(0, 0, 0),  # Fundo preto
                                text_color=(1, 1, 1),  # Texto branco
                                fontsize=8
                            )
                
                # Aplica todas as redações da página
                page.apply_redactions()
            
            # Adiciona metadados
            doc.set_metadata({
                'title': 'Nota Técnica Anonimizada',
                'subject': 'Documento com dados sensíveis removidos',
                'creator': 'Sistema de Notas Técnicas',
                'producer': 'PyMuPDF'
            })
            
            # Gera PDF anonimizado
            output = BytesIO()
            doc.save(output, garbage=4, deflate=True)
            doc.close()
            
            output.seek(0)
            return output.getvalue()
            
        except Exception as e:
            raise ValueError(f"Erro ao criar PDF anonimizado: {str(e)}")
