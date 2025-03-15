import os
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod


class PdfConverter():
    def __init__(self, pdf_dir, md_dir, img_dir):
        self.pdf_dir =pdf_dir
        self.pdf_name = os.path.basename(pdf_dir)

        self.md_dir = md_dir
        os.makedirs(self.md_dir, exist_ok=True) 

        self.img_dir = img_dir
        os.makedirs(self.img_dir, exist_ok=True)

        self.img_writer = FileBasedDataWriter(img_dir)
        self.md_writer = FileBasedDataWriter(md_dir)
        self.ds = PymuDocDataset(FileBasedDataReader("").read(pdf_dir))

    def convert(self):
        ## inference
        if self.ds.classify() == SupportedPdfParseMethod.OCR:
            infer_result = self.ds.apply(doc_analyze, ocr=True)

            ## pipeline
            pipe_result = infer_result.pipe_ocr_mode(self.img_writer)

        else:
            infer_result = self.ds.apply(doc_analyze, ocr=False)

            ## pipeline
            pipe_result = infer_result.pipe_txt_mode(self.img_writer)

        ### dump markdown
        md_content = pipe_result.get_markdown(self.img_dir)

        md_save_dir = os.path.join("..", "txt", self.pdf_name.split(".")[0] + ".txt")
        # 此时路径在md_writer下, 所以md_save_dir要是相对于md_writer的路径
        pipe_result.dump_md(self.md_writer, md_save_dir, self.img_dir)

        every_img_dir = []
        for item in os.listdir(self.img_dir):
            every_img_dir.append(os.path.join(self.img_dir, item))

        return md_save_dir, every_img_dir, md_content # 返回.md路径, 和每个图片的路径列表

        