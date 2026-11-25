"""Entirely fictional, code-generated resume used by onboarding and recordings."""
import fitz


def create_demo_pdf():
    doc=fitz.open()
    page=doc.new_page(width=595,height=842)
    ink=(.12,.20,.22);muted=(.40,.47,.48);green=(.12,.39,.34)
    def text(x,y,s,size=10,color=ink,bold=False):
        page.insert_text((x,y),s,fontname="china-s" if any(ord(c)>127 for c in s) else ("hebo" if bold else "helv"),fontsize=size,color=color)
    def section(y,s):
        text(42,y,s,13,green)
        page.draw_line((42,y+8),(553,y+8),color=(.82,.87,.84),width=.6)
    page.draw_rect(fitz.Rect(0,0,595,7),fill=green,color=green)
    text(42,32,"SYNTHETIC DEMO / ALL DETAILS ARE FICTIONAL",8,muted)
    text(42,72,"林小演",24)
    text(42,94,"算法工程实习 · 虚构示例简历",10,muted)
    text(42,116,"demo@example.com",10)
    text(200,116,"202-555-0148",10)
    text(42,136,"政治面貌：群众",10)
    text(200,136,"个人标识：",10)
    text(250,136,"demo_profile",10)
    text(42,156,"所在地：示例城市",10)
    avatar='<svg xmlns="http://www.w3.org/2000/svg" width="180" height="216"><rect width="180" height="216" rx="12" fill="#e0eee8"/><circle cx="90" cy="78" r="32" fill="#72a593"/><path d="M28 205v-30a62 62 0 0 1 124 0v30" fill="#72a593"/></svg>'
    with fitz.open(stream=avatar.encode(),filetype='svg') as image:
        page.insert_image(fitz.Rect(493,48,553,120),pixmap=image[0].get_pixmap())
    section(192,"教育背景")
    text(42,221,"示例理工大学 · 计算机科学",11)
    text(447,221,"2023 - 2027",9,muted)
    text(42,242,"课程：机器学习、数据结构、数据库、软件工程",10)
    section(280,"项目经历")
    text(42,310,"社区服务知识问答助手",12)
    text(447,310,"2025 - 2026",9,muted)
    text(42,334,"设计面向社区群众的知识问答流程，整理公开资料并构建检索索引。",10)
    text(42,356,"开发离线评估脚本，比较不同检索策略，记录答案质量与响应时间。",10)
    text(42,378,"实现来源引用与结果核查，让用户能够回到原始材料验证回答。",10)
    text(42,421,"文档质量检查工具",12)
    text(447,421,"2025",9,muted)
    text(42,445,"为虚构文档构建测试集，检查格式一致性、缺失字段与重复条目。",10)
    text(42,467,"编写脚本实现批处理与结果报告，加入错误恢复和回归测试。",10)
    section(510,"技术能力")
    text(42,540,"Python  /  Git  /  SQL  /  Linux",10)
    text(42,564,"熟悉检索评估、数据处理与自动化测试，能够编写可复现的实验脚本。",10)
    section(609,"演示说明")
    text(42,639,"本页全部信息由程序生成，不对应任何真实求职者。",10,muted)
    text(42,662,"联系方式采用保留域名与虚构号段，仅用于演示。",9,muted)
    text(42,685,"头像为几何图形；学校、项目、城市与个人标识均为虚构。",9,muted)
    text(42,790,"CleanCV · 本地脱敏演示素材",9,muted)
    doc.set_metadata({'title':'CleanCV synthetic demo','author':'Fictional sample'})
    result=doc.tobytes(garbage=4,deflate=True)
    doc.close()
    return result
