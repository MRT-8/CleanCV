"""Synthetic-only fixtures. Never put a real resume or portrait in the repository."""
import hashlib
import json
from pathlib import Path
import fitz
import pytest
from cleancv.core import analyze, clean_pdf, Region, CleanCVError
from cleancv.cli import main


def sample(rotation=0, scan=False, crop=False):
    d = fitz.open()
    p = d.new_page(width=595, height=842)
    p.insert_text((210, 52), "Alice Example", fontsize=20)
    p.insert_text((175, 80), "alice@example.test | +1 202-555-0187", fontsize=10)
    p.insert_text((180, 102), "13800138000", fontsize=10)
    p.insert_text((270, 102), "中共党员", fontname="china-s", fontsize=10)
    p.insert_text((40, 220), "Research and experience", fontsize=14)
    p.insert_text((40, 250), "Built a retrieval system; 2025.11 - 2026.11", fontsize=11)
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 50, 60), False)
    pix.clear_with(70)
    p.insert_image(fitz.Rect(500, 22, 560, 94), pixmap=pix)
    logo = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 120, 30), False)
    logo.clear_with(30)
    p.insert_image(fitz.Rect(30, 25, 150, 55), pixmap=logo)
    p.add_text_annot((40, 300), "secret in an annotation")
    p.insert_text((40, 340), "secret hidden text", render_mode=3)
    d.set_metadata({"author": "Alice Example", "title": "alice@example.test"})
    d.embfile_add("private.txt", b"secret attachment")
    p.insert_link({"kind": fitz.LINK_URI, "from": fitz.Rect(30, 30, 150, 55), "uri": "https://example.test/private"})
    if crop:
        p.set_cropbox(fitz.Rect(20, 10, 580, 820))
    p.set_rotation(rotation)
    if scan:
        pixels = p.get_pixmap()
        q = fitz.open()
        fresh = q.new_page(width=p.rect.width, height=p.rect.height)
        fresh.insert_image(fresh.rect, pixmap=pixels)
        data = q.tobytes()
        q.close()
    else:
        data = d.tobytes()
    d.close()
    return data


def test_detect_expected_and_keep_dates():
    a = analyze(sample())
    kinds = {r.kind for r in a.regions}
    assert {"name", "email", "phone", "politics", "photo"} <= kinds
    assert len([r for r in a.regions if r.kind == "photo"]) == 1
    assert not any(r.rect[1] > 180 for r in a.regions)
    report = json.dumps(a.to_dict())
    assert "alice@example.test" not in report and "Alice Example" not in report


def test_rebuilt_pdf_has_no_original_layers_or_metadata():
    data = sample()
    a = analyze(data)
    result = clean_pdf(data, a.regions)
    with fitz.open(stream=result, filetype="pdf") as d:
        assert len(d) == 1 and not d[0].get_text().strip()
        assert not d.embfile_count() and not d.get_toc()
        assert not d[0].get_links() and not list(d[0].annots() or [])
        assert not d.metadata.get("author")
        assert len(d[0].get_image_info()) == 1
        assert not d[0].get_fonts()
        pix = d[0].get_pixmap()
        assert pix.pixel(530, 50) == (255, 255, 255)  # portrait erased
        assert pix.pixel(80, 40) != (255, 255, 255)  # university-style logo retained
        crop = d[0].get_pixmap(clip=fitz.Rect(35, 205, 330, 260))
        assert min(crop.samples) < 80  # experience still visually present
        objects = b"".join(d.xref_object(i).encode() for i in range(1, d.xref_length()))
        assert b"Alice Example" not in objects
        assert b"private.txt" not in objects


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
@pytest.mark.parametrize("crop", [False, True])
def test_manual_regions_follow_display_coordinates(rotation, crop):
    data = sample(rotation=rotation, crop=crop)
    with fitz.open(stream=data, filetype="pdf") as d:
        p = d[0]
        # Locate the portrait in displayed coordinates.
        image = next(x for x in p.get_image_info() if x['width'] == 50)
        display = (fitz.Rect(image['bbox']) * p.rotation_matrix) & p.rect
        width, height = p.rect.width, p.rect.height
    result = clean_pdf(data, [Region(1, tuple(display))], dpi=144)
    with fitz.open(stream=result, filetype="pdf") as d:
        assert abs(d[0].rect.width - width) < .1
        assert abs(d[0].rect.height - height) < .1
        pix = d[0].get_pixmap()
        assert pix.pixel(int((display.x0+display.x1)/2), int((display.y0+display.y1)/2)) == (255,255,255)


def test_scanned_pdf_requires_explicit_review_in_cli(tmp_path):
    source = tmp_path/'source.pdf';source.write_bytes(sample(scan=True))
    output = tmp_path/'clean.pdf'
    assert analyze(source.read_bytes()).pages[0]['scan_like']
    assert main(['clean',str(source),'-o',str(output)]) == 2
    assert not output.exists()
    assert main(['clean',str(source),'-o',str(output),'--box','1:160,20,570,120','--allow-scanned']) == 0


def test_invalid_regions_and_input():
    for value in [{'page':0,'rect':[1,2,3,4]}, {'page':1,'rect':[-1,1,30,40]}, {'page':2,'rect':[1,1,30,40]}]:
        with pytest.raises(CleanCVError):
            clean_pdf(sample(),[Region.from_dict(value)])
    with pytest.raises(CleanCVError):
        Region.from_dict({'page':1,'rect':[0,0,float('nan'),20]})
    with pytest.raises(CleanCVError):
        analyze(b'not a PDF')


def test_cli_preserves_source_and_refuses_overwrite(tmp_path,capsys):
    source=tmp_path/'source.pdf';data=sample();source.write_bytes(data)
    assert main(['clean',str(source),'-o',str(source),'--force']) == 2
    assert source.read_bytes()==data
    output=tmp_path/'clean.pdf'
    assert main(['clean',str(source),'-o',str(output)]) == 0
    before=output.read_bytes()
    assert main(['clean',str(source),'-o',str(output)]) == 2
    assert output.read_bytes()==before
    captured=capsys.readouterr()
    assert 'alice@example.test' not in captured.out+captured.err


def test_plan_is_bound_to_input(tmp_path):
    source=tmp_path/'source.pdf';source.write_bytes(sample())
    plan=tmp_path/'selection.plan.json'
    assert main(['scan',str(source),'--plan',str(plan)]) == 0
    value=json.loads(plan.read_text());value['document_sha256']='wrong';plan.write_text(json.dumps(value))
    out=tmp_path/'clean.pdf'
    assert main(['clean',str(source),'-o',str(out),'--plan',str(plan)])==2
    assert not out.exists()


def test_extra_terms_and_all_images():
    a=analyze(sample(),terms=['retrieval system'],images='all')
    assert any(r.kind=='extra' for r in a.regions)
    assert len([r for r in a.regions if r.kind in {'photo','image'}])==2


def test_multi_page_output():
    with fitz.open(stream=sample(),filetype='pdf') as d:
        with fitz.open(stream=sample(),filetype='pdf') as another:
            d.insert_pdf(another)
        data=d.tobytes()
    a=analyze(data,names=['Alice Example'])
    assert any(r.kind=='name' and r.page==2 for r in a.regions)
    with fitz.open(stream=clean_pdf(data,a.regions),filetype='pdf') as result:
        assert len(result)==2


def test_existing_opaque_annotation_never_reveals_underlying_text():
    d=fitz.open();p=d.new_page(width=400,height=400)
    p.insert_text((30,60),'SECRET UNDER COVER',fontsize=15)
    p.insert_text((30,160),'Visible experience',fontsize=12)
    cover=p.add_rect_annot(fitz.Rect(20,35,290,75))
    cover.set_colors(stroke=(1,1,1),fill=(1,1,1));cover.set_border(width=0);cover.set_opacity(1);cover.update()
    data=d.tobytes();d.close()
    result=clean_pdf(data,[Region(1,(300,300,320,320))])
    with fitz.open(stream=result,filetype='pdf') as output:
        hidden_area=output[0].get_pixmap(clip=fitz.Rect(25,40,280,70))
        assert min(hidden_area.samples)==255
        visible_area=output[0].get_pixmap(clip=fitz.Rect(25,145,220,165))
        assert min(visible_area.samples)<100


def test_visible_form_email_is_detected_and_removed():
    d=fitz.open();p=d.new_page(width=595,height=842)
    p.insert_text((40,230),'Research and engineering experience',fontsize=12)
    w=fitz.Widget();w.field_name='contact';w.field_type=fitz.PDF_WIDGET_TYPE_TEXT
    w.field_value='alice@example.test';w.rect=fitz.Rect(100,50,320,80);w.text_font='Helv';w.text_fontsize=12
    p.add_widget(w);data=d.tobytes();d.close()
    a=analyze(data)
    assert any(r.kind=='email' for r in a.regions)
    with fitz.open(stream=clean_pdf(data,a.regions),filetype='pdf') as output:
        area=output[0].get_pixmap(clip=fitz.Rect(100,50,320,80))
        assert min(area.samples)==255
        assert not list(output[0].widgets() or [])
