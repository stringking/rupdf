//! Benchmarks for rupdf rendering.
//!
//! Run with: cargo bench
//!
//! Note: These benchmarks are NOT part of CI gating.
//! Results are for development reference only.

// Note: These benchmarks require the crate to be built as rlib.
// Since rupdf is primarily a cdylib for Python, these benchmarks
// test component-level performance rather than full rendering.

use criterion::{black_box, criterion_group, criterion_main, Criterion};

/// Benchmark Color conversion operations
fn bench_color_operations(c: &mut Criterion) {
    c.bench_function("color_to_rgb_floats", |b| {
        // Simulate color conversion (can't import from cdylib)
        b.iter(|| {
            let r: u8 = 128;
            let g: u8 = 64;
            let b_val: u8 = 255;
            let result = (
                black_box(r) as f32 / 255.0,
                black_box(g) as f32 / 255.0,
                black_box(b_val) as f32 / 255.0,
            );
            black_box(result)
        })
    });
}

/// Benchmark zlib compression (used in PDF streams)
fn bench_compression(c: &mut Criterion) {
    let data: Vec<u8> = (0..10000).map(|i| (i % 256) as u8).collect();

    c.bench_function("zlib_compress_10kb", |b| {
        b.iter(|| {
            let compressed = miniz_oxide::deflate::compress_to_vec_zlib(black_box(&data), 6);
            black_box(compressed)
        })
    });
}

/// Benchmark basic PDF content stream operations
fn bench_content_stream(c: &mut Criterion) {
    use pdf_writer::Content;

    c.bench_function("content_stream_rects_100", |b| {
        b.iter(|| {
            let mut content = Content::new();
            for i in 0..100 {
                let x = (i % 10) as f32 * 50.0;
                let y = (i / 10) as f32 * 50.0;
                content.set_fill_rgb(0.5, 0.5, 0.5);
                content.rect(x, y, 40.0, 40.0);
                content.fill_nonzero();
            }
            black_box(content.finish())
        })
    });

    c.bench_function("content_stream_text_50", |b| {
        b.iter(|| {
            let mut content = Content::new();
            for i in 0..50 {
                content.begin_text();
                content.set_font(pdf_writer::Name(b"F1"), 12.0);
                content.next_line(72.0, 700.0 - i as f32 * 14.0);
                content.show(pdf_writer::Str(b"Hello World Test Line"));
                content.end_text();
            }
            black_box(content.finish())
        })
    });
}

/// Benchmark PDF document creation
fn bench_pdf_creation(c: &mut Criterion) {
    use pdf_writer::{Finish, Name, Pdf, Rect, Ref};

    c.bench_function("pdf_empty_page", |b| {
        b.iter(|| {
            let mut pdf = Pdf::new();
            let catalog = Ref::new(1);
            let pages = Ref::new(2);
            let page = Ref::new(3);
            let content = Ref::new(4);

            pdf.catalog(catalog).pages(pages);

            let mut pages_obj = pdf.pages(pages);
            pages_obj.kids([page]);
            pages_obj.count(1);
            pages_obj.finish();

            pdf.stream(content, b"");

            let mut page_obj = pdf.page(page);
            page_obj.parent(pages);
            page_obj.media_box(Rect::new(0.0, 0.0, 612.0, 792.0));
            page_obj.contents(content);
            page_obj.finish();

            black_box(pdf.finish())
        })
    });

    c.bench_function("pdf_10_pages", |b| {
        b.iter(|| {
            let mut pdf = Pdf::new();
            let catalog = Ref::new(1);
            let pages_ref = Ref::new(2);

            pdf.catalog(catalog).pages(pages_ref);

            let page_refs: Vec<Ref> = (0..10).map(|i| Ref::new(3 + i * 2)).collect();
            let content_refs: Vec<Ref> = (0..10).map(|i| Ref::new(4 + i * 2)).collect();

            let mut pages_obj = pdf.pages(pages_ref);
            pages_obj.kids(page_refs.iter().copied());
            pages_obj.count(10);
            pages_obj.finish();

            for i in 0..10 {
                pdf.stream(content_refs[i], b"BT /F1 12 Tf 72 700 Td (Page) Tj ET");

                let mut page_obj = pdf.page(page_refs[i]);
                page_obj.parent(pages_ref);
                page_obj.media_box(Rect::new(0.0, 0.0, 612.0, 792.0));

                let mut resources = page_obj.resources();
                let mut fonts = resources.fonts();
                fonts.pair(Name(b"F1"), Ref::new(100));
                fonts.finish();
                resources.finish();

                page_obj.contents(content_refs[i]);
                page_obj.finish();
            }

            black_box(pdf.finish())
        })
    });
}

criterion_group!(
    benches,
    bench_color_operations,
    bench_compression,
    bench_content_stream,
    bench_pdf_creation,
);

criterion_main!(benches);
