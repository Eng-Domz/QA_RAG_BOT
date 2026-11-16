"use client";

import { useState } from "react";

type Language = "en" | "ar";
type DocumentStatus = "ready" | "processing" | "failed";

interface DocumentSummary {
  id: string;
  title: Record<Language, string>;
  detail: Record<Language, string>;
  status: DocumentStatus;
  progress?: number;
}

const copy = {
  en: {
    workspace: "My study material",
    subtitle: "Three explicit API states shown with typed data.",
    languageLabel: "Interface language",
    documents: "Documents",
    addDocument: "Add document",
    ready: "Ready",
    processing: "Processing",
    failed: "Needs attention",
    askTitle: "Ask your material",
    askPlaceholder: "What is the difference between TCP and UDP?",
    askButton: "Ask with citations",
    sourceLabel: "Example source",
    sourceText: "Computer Networks · Lecture 04 · page 18",
    previewNote: "Static preview — the backend connection comes next.",
  },
  ar: {
    workspace: "موادي الدراسية",
    subtitle: "ثلاث حالات واضحة لواجهة البرمجة ممثلة ببيانات محددة النوع.",
    languageLabel: "لغة الواجهة",
    documents: "المستندات",
    addDocument: "إضافة مستند",
    ready: "جاهز",
    processing: "قيد المعالجة",
    failed: "يحتاج إلى مراجعة",
    askTitle: "اسأل في محتوى موادك",
    askPlaceholder: "ما الفرق بين بروتوكولي TCP و UDP؟",
    askButton: "اسأل مع المراجع",
    sourceLabel: "مثال للمرجع",
    sourceText: "شبكات الحاسب · المحاضرة ٤ · صفحة ١٨",
    previewNote: "نموذج ثابت — سيتم ربط الواجهة بالخادم في المرحلة القادمة.",
  },
} as const satisfies Record<Language, Record<string, string>>;

const documents = [
  {
    id: "networks",
    title: { en: "Computer Networks", ar: "شبكات الحاسب" },
    detail: { en: "24 pages · PDF", ar: "٢٤ صفحة · PDF" },
    status: "ready",
  },
  {
    id: "databases",
    title: { en: "Database Systems", ar: "نظم قواعد البيانات" },
    detail: { en: "Indexing 18 of 30 pages", ar: "تمت فهرسة ١٨ من ٣٠ صفحة" },
    status: "processing",
    progress: 60,
  },
  {
    id: "security",
    title: { en: "Security Notes", ar: "ملاحظات أمن المعلومات" },
    detail: { en: "The PDF has no extractable text", ar: "ملف PDF لا يحتوي نصاً قابلاً للاستخراج" },
    status: "failed",
  },
] as const satisfies ReadonlyArray<DocumentSummary>;

function StatusBadge({ status, language }: { status: DocumentStatus; language: Language }) {
  return (
    <span className={`status-badge status-${status}`}>
      <span aria-hidden="true" />
      {copy[language][status]}
    </span>
  );
}

export function StudyWorkspacePreview() {
  const [language, setLanguage] = useState<Language>("en");
  const text = copy[language];
  const direction = language === "ar" ? "rtl" : "ltr";

  return (
    <div className="workspace-preview" lang={language} dir={direction}>
      <header className="workspace-toolbar">
        <div>
          <p>{text.workspace}</p>
          <span>{text.subtitle}</span>
        </div>

        <div className="language-control" role="group" aria-label={text.languageLabel}>
          <button
            type="button"
            aria-pressed={language === "en"}
            onClick={() => setLanguage("en")}
          >
            EN
          </button>
          <button
            type="button"
            aria-pressed={language === "ar"}
            onClick={() => setLanguage("ar")}
          >
            عربي
          </button>
        </div>
      </header>

      <div className="workspace-grid">
        <section className="document-panel" aria-labelledby="document-heading">
          <div className="panel-heading">
            <h3 id="document-heading">{text.documents}</h3>
            <button type="button" disabled title={text.previewNote}>
              <span aria-hidden="true">＋</span>
              {text.addDocument}
            </button>
          </div>

          <div className="document-list">
            {documents.map((document) => (
              <article className="document-card" key={document.id}>
                <div className="document-icon" aria-hidden="true">
                  {document.title[language].slice(0, 1)}
                </div>
                <div className="document-copy">
                  <h4>{document.title[language]}</h4>
                  <p>{document.detail[language]}</p>
                  {document.status === "processing" ? (
                    <div
                      className="progress-track"
                      role="progressbar"
                      aria-label={document.detail[language]}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-valuenow={document.progress}
                    >
                      <span style={{ width: `${document.progress}%` }} />
                    </div>
                  ) : null}
                </div>
                <StatusBadge status={document.status} language={language} />
              </article>
            ))}
          </div>
        </section>

        <section className="question-panel" aria-labelledby="question-heading">
          <span className="question-number" aria-hidden="true">
            01
          </span>
          <h3 id="question-heading">{text.askTitle}</h3>
          <label htmlFor="prototype-question" className="sr-only">
            {text.askTitle}
          </label>
          <textarea
            id="prototype-question"
            placeholder={text.askPlaceholder}
            rows={4}
            disabled
          />
          <button type="button" disabled title={text.previewNote}>
            {text.askButton}
            <span aria-hidden="true">↗</span>
          </button>

          <div className="source-preview">
            <p>{text.sourceLabel}</p>
            <span>{text.sourceText}</span>
          </div>
          <p className="preview-note" role="note">
            {text.previewNote}
          </p>
        </section>
      </div>
    </div>
  );
}
