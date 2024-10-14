import os
import docx2txt
import jieba
from whoosh import index
from whoosh.analysis import Tokenizer, Token
from whoosh.fields import Schema, TEXT, ID, KEYWORD
from whoosh.qparser import QueryParser
from docx import Document
import pandas as pd
import PyPDF2
from striprtf.striprtf import rtf_to_text
import textract
import openpyxl
import thulac
from whoosh.query import Term, Or, Phrase, And

from MDLStore.utils import EmailParser

# 清华智能中文分词器
thu = thulac.thulac(seg_only=True)
class CustomTokenizer:
    @staticmethod
    def enumerate_splits(text_, start=0):
        """
        递归地枚举给定中文字符串的所有分词组合。
        :param text_: 要分词的中文字符串。
        :param start: 当前递归开始的位置。
        :return: 生成所有可能的分词结果。
        """
        if start == len(text_):
            yield []
        else:
            for end in range(start + 1, len(text_) + 1):
                word = text_[start:end]
                for rest in CustomTokenizer.enumerate_splits(text_, end):
                    yield [word] + rest

    @staticmethod
    def get_chinese_token_list(text_):
        return list(CustomTokenizer.enumerate_splits(text_))

    @staticmethod
    def smart_jieba_tokenizer(text_):
        # 使用精确模式进行分词
        tokens_ = jieba.cut(text_, cut_all=False)
        # tokens_ = jieba.cut_for_search(text_)
        return list(tokens_)

    @staticmethod
    def smart_thu_tokenizer(text_):
        # Initialize THULAC with default model
        # thu_ = thulac.thulac(seg_only=True)  # Set seg_only to True for tokenization without POS tagging
        # Tokenize the text
        tokens_ = thu.cut(text_, text=True)  # The text=True parameter returns the result as a string
        # Split the string into a list of tokens
        token_list = tokens_.split()
        return token_list

    @staticmethod
    def get_merge_tokens(text_):
        # tokens1 = CustomTokenizer.smart_thu_tokenizer(text_)
        # tokens2 = CustomTokenizer.smart_jieba_tokenizer(text_)
        pass


class FileInfo:
    """
    用于向索引库添加索引信息，与数据库附件文件表不同
    """

    def __init__(self, attachment_id, email_id, filename, attachment_type, file_path, content):
        self.attachment_id = attachment_id
        self.email_id = email_id
        self.filename = filename
        self.attachment_type = attachment_type
        self.file_path = file_path
        self.content = content

    def __str__(self):
        # 安全地处理 content 字段，如果是 None，使用空字符串
        content_preview = (self.content[:50] + '...') if self.content is not None else 'None'
        return (f"FileInfo(attachment_id={self.attachment_id}, email_id={self.email_id}, "
                f"filename={self.filename}, attachment_type={self.attachment_type}, "
                f"file_path={self.file_path}, content={content_preview})")


class FileReader:
    @staticmethod
    def read_docx(file_path):
        doc = Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return "\n".join(full_text)

    @staticmethod
    def read_pdf(file_path):
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            full_text = []
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                full_text.append(page.extract_text())
        return "\n".join(full_text)

    @staticmethod
    def read_excel(file_path):
        df = pd.read_excel(file_path)
        # 将 DataFrame 转换为字符串并返回
        return df.to_string()

    @staticmethod
    def read_doc(file_path):
        try:
            # 使用 docx2txt 处理 .doc 文件
            text = docx2txt.process(file_path)
            return text
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            return ""

    @staticmethod
    def read_rtf(file_path):
        try:
            absolute_path = os.path.abspath(file_path)
            # normalized_path = os.path.normpath(file_path)
            # 打开并读取 RTF 文件内容
            with open(absolute_path, 'r', encoding='utf-8') as file:
                rtf_content = file.read()
                text = rtf_to_text(rtf_content)
                return text
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            return ""

    @staticmethod
    def read_eml(file_path):
        with open(file_path, 'rb') as file:
            raw_email = file.read()
        email_parser = EmailParser(raw_email)
        body_parts = email_parser.get_body()
        len_body = len(body_parts)
        if len_body == 0:
            return ""
        if len_body >= 3:
            html_index = int(len_body / 2) - 1
        else:
            html_index = len_body - 1
        combined_str = ''.join(body_parts[:html_index + 1])
        return combined_str

    @staticmethod
    def read_with_textract(file_path):
        # 获取文件扩展名
        print(f'打印邮件附件内容{file_path}')
        file_extension = os.path.splitext(file_path)[-1].lower()
        # 定义不处理的文件类型
        unsupported_types = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.mp4', '.avi', '.mov', '.mkv', '.mp3', '.wav',
                             '.flac', '.zip', '.7z', '.py', '.cpp', '.java']

        # 如果文件类型不支持，返回空字符串
        if file_extension in unsupported_types:
            return ""

        # 处理其他文件类型
        try:
            text = textract.process(file_path).decode("utf-8")
            return text
        except Exception as e:
            # 捕获并处理可能的异常
            print(f"Error processing file {file_path}: {e}")
            return ""



class ThulacTokenizer(Tokenizer):
    def __call__(self, value, positions=False, chars=False, keeporiginal=False, removestops=True, start_pos=0,
                 start_char=0, mode='', **kwargs):
        t = Token(positions, chars, removestops=removestops, mode=mode)
        pos = start_pos
        char_pos = start_char
        for word in thu.cut(value):
            t.text = word[0]
            t.stopped = False
            if positions:
                t.pos = pos
                pos += 1
            if chars:
                t.startchar = char_pos
                t.endchar = char_pos + len(word[0])
                char_pos += len(word[0])
            yield t


def thulac_analyzer():
    return ThulacTokenizer()


class IndexManager:
    def __init__(self, drive):
        """
        全文索引管理器v1.0
        :param drive: 磁盘分区字母，例如‘E’
        """
        self.base_drive = drive
        self.index_dir = os.path.join(f'{drive}:/', 'MDLStore', 'index', "attach_index")
        os.makedirs(self.index_dir, exist_ok=True)

        # 配置项
        self.common_search_terms_on = False
        self.position_search_terms_on = True

        attachment_schema = Schema(
            attachment_id=ID(stored=True, unique=True),  # 附件标识符，存储并唯一
            email_id=ID(stored=True),  # 所属邮件标识符，存储
            filename=KEYWORD(stored=True),  # 附件文件名，存储并全文索引
            attachment_type=KEYWORD(stored=True),  # 附件类型，存储
            file_path=ID(stored=True),  # 文件存储路径，存储并全文索引
            # content=TEXT(stored=False, analyzer=self.analyzer, vector="positions")
            content=TEXT(stored=False, analyzer=thulac_analyzer(), vector="positions")
        )

        self.schema = attachment_schema
        if index.exists_in(self.index_dir):
            self.ix = index.open_dir(self.index_dir)
        else:
            self.ix = index.create_in(self.index_dir, self.schema)

    def add_to_index(self, file_path, file_info=None):
        """
        添加索引
        :param file_info: 文件信息对象
        :param file_path: 文件绝对路径
        :return: None
        """
        file_path = os.path.abspath(file_path)
        if file_path.endswith(".docx"):
            content = FileReader.read_docx(file_path)
        elif file_path.endswith(".pdf"):
            content = FileReader.read_pdf(file_path)
        elif file_path.endswith(".xlsx"):
            content = FileReader.read_excel(file_path)
        elif file_path.endswith(".doc"):
            content = FileReader.read_doc(file_path)
        elif file_path.endswith(".rtf"):
            content = FileReader.read_rtf(file_path)
        elif file_path.endswith(".eml"):
            content = FileReader.read_eml(file_path)
        else:
            content = FileReader.read_with_textract(file_path)

        def clean_content(content_):
            if isinstance(content_, str):
                # 替换无法编码的字符
                return content_.encode('utf-8', 'replace').decode('utf-8')
            return content_

        # 使用清理后的内容
        content = clean_content(content)

        writer = self.ix.writer()

        # print(file_info)
        writer.update_document(
            attachment_id=file_info.attachment_id,
            email_id=file_info.email_id,
            filename=file_info.filename,
            attachment_type=file_info.attachment_type,
            file_path=file_info.file_path,
            content=content
        )
        # writer.commit(optimize=True)
        writer.commit()
        # 打印索引构建信息
        print(f"Indexed: {file_info.attachment_id}")

    def search_index(self, query_phrase):
        """
        查询索引（测试用法，一般不调用）
        :param query_phrase: 查询短语
        :return:
        """
        with self.ix.searcher() as searcher:
            # 使用短语搜索，确保查询字符串保持原始形式（原串由空格分隔）
            # words = query_phrase.split()
            # 使用自定义分词器对输入信息进行分词
            words = CustomTokenizer().smart_thu_tokenizer(query_phrase)
            print(words)
            myquery = Phrase("content", words)
            # 执行搜索
            results = searcher.search(myquery, terms=self.position_search_terms_on)
            for result in results:
                print(f"Title: {result['filename']}, Path: {result['file_path']}")

                # # 获取匹配词在当前文档中的位置
                # matched_terms = result.matched_terms()  # 获取匹配的词
                # print(matched_terms)
                # for field_name, text in matched_terms:
                #     if field_name == 'content':  #只处理内容字段
                #         text_str = text.decode('utf-8')
                #         vector = searcher.vector(result.docnum, field_name)
                #         if vector is not None:
                #             # 定位到匹配的词条
                #             vector.skip_to(text_str)
                #             if vector.id() == text_str:
                #                 positions = list(vector.value_as("positions"))
                #                 print(f"匹配词: {text_str}, 位置: {positions}")

                # #获取全部分词
                # docnum = result.docnum  # 获取搜索结果的文档编号
                # vector = searcher.vector(docnum, "content")  # 获取 'content' 字段的词向量
                # if vector is not None:
                #     # 遍历词向量中的所有词条及其位置信息
                #     while vector.is_active():
                #         # 获取当前位置的词条和频率信息
                #         term_text = vector.id()
                #         positions = list(vector.value_as("positions"))
                #         print(f"Term: {term_text}, Positions: {positions}")
                #         vector.next()

    def search_file(self, query_phrase, file_path_list=None):
        """
        在文件路径列表所指示的文件中执行全文检索，若参数为空，则表示检索所有索引
        :param query_phrase: 查询语句
        :param file_path_list: 文档路径列表
        :return: 查询结果详情列表
        """
        # print(f'文件路径列表为{file_path_list},类型为{type(file_path_list)}')

        with self.ix.searcher() as searcher:
            words = CustomTokenizer().smart_thu_tokenizer(query_phrase)
            print(words)
            content_query = Phrase("content", words)
            # 执行搜索
            if file_path_list:
                # 去除 None 项并去重
                file_path_list = list(set([file_path for file_path in file_path_list if file_path is not None]))
                print(file_path_list)
                # 创建一个查询，匹配任何一个提供的路径
                path_queries = [Term("file_path", path) for path in file_path_list]
                # print(path_queries)
                # 使用 Or 查询组合所有路径查询
                path_query = Or(path_queries)
                # 使用 And 查询结合内容查询和路径查询
                combined_query = And([content_query, path_query])
                print(f'combined_query={combined_query}')
                # print(combined_query)
                results = searcher.search(combined_query, terms=self.common_search_terms_on, limit=None)
            else:
                # 如果没有提供路径列表，仅搜索内容
                results = searcher.search(content_query, terms=self.common_search_terms_on, limit=None)

            result_list = []
            for result in results:
                # print(f"Title: {result['filename']}, Path: {result['file_path']}")
                result_dict = {
                    'attachment_id': result['attachment_id'],
                    'email_id': result['email_id'],
                    'filename': result['filename'],
                    'attachment_type': result['attachment_type'],
                    'file_path': result['file_path'],
                    'content': None
                }
                result_list.append(result_dict)
            return result_list

    def search_file_paged(self, content_keyword, file_path_list=None, page=1, page_size=10):
        """
        在文件路径列表所指示的文件中执行全文检索，支持分页。
        若参数为空，则表示检索所有索引。
        :param content_keyword: 需要检索的内容关键字
        :param file_path_list: 文件路径列表
        :param page: 当前页码
        :param page_size: 每页显示的文档数量
        :return: 检索结果详情列表，结果个数，页数
        """
        with self.ix.searcher() as searcher:
            words = CustomTokenizer().smart_thu_tokenizer(content_keyword)
            # print("搜索词:", words)
            content_query = Phrase("content", words)

            # 根据是否有文件路径列表来构建查询
            if file_path_list:
                path_queries = [Term("file_path", path) for path in file_path_list]
                path_query = Or(path_queries)
                combined_query = And([content_query, path_query])
                results = searcher.search_page(combined_query, page,
                                               pagelen=page_size, terms=self.common_search_terms_on)
            else:
                results = searcher.search_page(content_query, page,
                                               pagelen=page_size, terms=self.common_search_terms_on)

            # print(f"总结果数: {results.total}")
            # print(f"总页数: {results.pagecount}")

            # 打印并返回搜索结果
            result_list = []
            for result in results:
                # print(f"Title: {result['filename']}, Path: {result['file_path']}")
                result_dict = {
                    'attachment_id': result['attachment_id'],
                    'email_id': result['email_id'],
                    'filename': result['filename'],
                    'attachment_type': result['attachment_type'],
                    'file_path': result['file_path'],
                    'content': None
                }
                result_list.append(result_dict)
            return result_list, results.total, results.pagecount

    def get_term_positions(self, query_string, attachment_id):
        """
        获取查询词在指定附件中的位置。
        :param query_string: 查询的字符串
        :param attachment_id: 附件的唯一标识符
        :return: 词的位置列表
        """
        with self.ix.searcher() as searcher:
            # 使用分词器对查询字符串进行分词
            query_terms = CustomTokenizer().smart_thu_tokenizer(query_string)
            # 构建内容查询
            content_query = And([Phrase("content", query_terms), Term("attachment_id", attachment_id)])

            # 执行查询
            results = searcher.search(content_query, terms=self.position_search_terms_on, limit=None)

            position_list = []
            for result in results:
                print(f"Title: {result['filename']}, Path: {result['file_path']}")
                # 获取匹配词在当前文档中的位置
                matched_terms = result.matched_terms()  # 获取匹配的词
                # print(matched_terms)
                for field_name, text in matched_terms:
                    if field_name == 'content':  # 只处理内容字段
                        text_str = text.decode('utf-8')
                        vector = searcher.vector(result.docnum, field_name)
                        if vector is not None:
                            # 定位到匹配的词条
                            vector.skip_to(text_str)
                            if vector.id() == text_str:
                                positions = list(vector.value_as("positions"))
                                position_dict = {
                                    'Term': text_str,
                                    'Positions': positions
                                }
                                position_list.append(position_dict)
                                # print(f"匹配词: {text_str}, 位置: {positions}")
            return position_list

    @staticmethod
    def display_tokens(file_path):
        """
        读取文件并显示分词结果
        :param file_path: 文件绝对路径
        :return: None
        """
        # 读取文件内容
        if file_path.endswith(".docx"):
            content = FileReader.read_docx(file_path)
        elif file_path.endswith(".pdf"):
            content = FileReader.read_pdf(file_path)
        elif file_path.endswith(".xlsx"):
            content = FileReader.read_excel(file_path)
        elif file_path.endswith(".doc"):
            content = FileReader.read_doc(file_path)
        elif file_path.endswith(".rtf"):
            content = FileReader.read_rtf(file_path)
        else:
            content = FileReader.read_with_textract(file_path)

        print(content)

        # 获取自定义分词器
        # tokenizer = ThuTokenizer()
        # tokens = list(tokenizer(content))
        #
        # # 打印分词结果
        # print(f"Tokens for {file_path}:")
        # for token in tokens:
        #     print(token.text)

    def list_all_documents(self):
        """
        列出所有索引中的文档
        :return: None
        """
        with self.ix.searcher() as searcher:
            results = searcher.search(QueryParser("content", self.ix.schema).parse("*"))
            for result in results:
                print(f"Document: {result}")


