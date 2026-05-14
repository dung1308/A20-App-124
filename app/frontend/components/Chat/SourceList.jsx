import React from 'react';

const getHostLabel = (url) => {
  if (!url) return 'VinUni admissions';

  try {
    const host = new URL(url).hostname.replace(/^www\./, '');
    if (host.includes('admissions.vinuni.edu.vn')) return 'VinUni Admissions';
    if (host.includes('vinuni.edu.vn')) return 'VinUni';
    return host;
  } catch {
    return 'Tài liệu tham khảo';
  }
};

const formatDate = (value) => {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleDateString('vi-VN');
};

const sourceTitle = (source, index) => {
  if (typeof source === 'string') return source;
  return (
    source.title ||
    source.name ||
    source.document_title ||
    source.source ||
    source.url ||
    `Nguồn ${index + 1}`
  );
};

const sourceSnippet = (source) => {
  if (!source || typeof source === 'string') return null;
  return source.snippet || source.summary || source.text_preview || source.excerpt || null;
};

const normalizeSource = (source, index) => {
  const url = typeof source === 'string' ? source : source?.url || source?.link || '';
  return {
    key: `${url || sourceTitle(source, index)}-${index}`,
    title: sourceTitle(source, index),
    url,
    host: getHostLabel(url),
    date: formatDate(source?.date || source?.updated_at || source?.retrieved_at),
    snippet: sourceSnippet(source),
  };
};

const SourceList = ({ sources = [], compact = false, showEmpty = false }) => {
  const cleanSources = sources.filter(Boolean).map(normalizeSource);

  if (cleanSources.length === 0) {
    if (!showEmpty) return null;

    return (
      <div className="mt-3 rounded-xl border border-amber-100 bg-amber-50/70 px-3 py-2 text-xs text-amber-800">
        <div className="flex items-start gap-2">
          <span className="material-symbols-outlined text-[17px] mt-0.5">info</span>
          <p>Chưa có nguồn chính thức được đính kèm cho câu trả lời này. Với thông tin tuyển sinh quan trọng, bạn nên kiểm tra lại trên trang VinUni.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`${compact ? 'mt-3' : 'mt-4'} rounded-xl border border-blue-100 bg-blue-50/40 overflow-hidden`}>
      <div className="px-3 py-2 border-b border-blue-100 bg-white/70 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className="material-symbols-outlined text-[18px] text-blue-700">verified</span>
          <div className="min-w-0">
            <p className="text-xs font-bold text-slate-800">Nguồn đã tham khảo</p>
            <p className="text-[11px] text-slate-500 truncate">Dùng để bạn kiểm tra lại thông tin chính thức</p>
          </div>
        </div>
        <span className="shrink-0 rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-blue-700">
          {cleanSources.length} nguồn
        </span>
      </div>

      <div className="divide-y divide-blue-100/80">
        {cleanSources.map((source, index) => {
          const content = (
            <div className="block px-3 py-2.5 hover:bg-white/70 transition-colors">
              <div className="flex items-start gap-2">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-white text-[11px] font-bold text-blue-700 border border-blue-100">
                  {index + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                    <p className="font-semibold text-[12px] text-slate-800 line-clamp-1">
                      {source.title}
                    </p>
                    <span className="rounded bg-white px-1.5 py-0.5 text-[10px] font-medium text-slate-500 border border-slate-100">
                      {source.host}
                    </span>
                    {source.date && (
                      <span className="text-[10px] text-slate-500">Cập nhật {source.date}</span>
                    )}
                  </div>
                  {source.snippet && (
                    <p className="mt-1 text-[11px] leading-snug text-slate-600 line-clamp-2">
                      {source.snippet}
                    </p>
                  )}
                  {source.url && (
                    <p className="mt-1 text-[11px] font-medium text-blue-700 flex items-center gap-1">
                      Mở nguồn
                      <span className="material-symbols-outlined text-[13px]">open_in_new</span>
                    </p>
                  )}
                </div>
              </div>
            </div>
          );

          return source.url ? (
            <a key={source.key} href={source.url} target="_blank" rel="noopener noreferrer" className="block">
              {content}
            </a>
          ) : (
            <div key={source.key}>{content}</div>
          );
        })}
      </div>

      <div className="px-3 py-2 bg-white/60 text-[11px] text-slate-500 flex items-start gap-1.5">
        <span className="material-symbols-outlined text-[14px] mt-0.5">fact_check</span>
        <span>AI có thể tóm tắt chưa đầy đủ. Hãy ưu tiên thông tin trên trang chính thức khi ra quyết định.</span>
      </div>
    </div>
  );
};

export default SourceList;
