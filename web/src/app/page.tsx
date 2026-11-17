import { StudyWorkspacePreview } from "@/app/components/study-workspace-preview";

const principles = [
  {
    number: "01",
    title: "Ask naturally",
    body: "Use Arabic, English, or both without translating your notes first.",
  },
  {
    number: "02",
    title: "Check the evidence",
    body: "Every supported answer points back to the document passage it used.",
  },
  {
    number: "03",
    title: "Trust a refusal",
    body: "When the material is not enough, the platform says so clearly.",
  },
] as const;

export default function Home() {
  return (
    <main>
      <section className="hero-shell">
        <nav className="topbar" aria-label="Primary navigation">
          <a className="brand" href="#top" aria-label="Dalil home">
            <span className="brand-mark" aria-hidden="true">
              د
            </span>
            <span>
              <strong>Dalil</strong>
              <small>Bilingual knowledge</small>
            </span>
          </a>
          <a className="text-link" href="#workspace">
            View interface prototype
            <span aria-hidden="true">↘</span>
          </a>
        </nav>

        <div id="top" className="hero-grid">
          <div className="hero-copy">
            <p className="eyebrow">Your notes. Your language. Verifiable answers.</p>
            <h1>
              Study across languages,
              <span> without losing the source.</span>
            </h1>
            <p className="hero-lede">
              Dalil turns Arabic and English course material into a focused
              study workspace. Ask a question, inspect the evidence, and know
              when the documents cannot support an answer.
            </p>
            <div className="hero-actions">
              <a className="primary-action" href="#workspace">
                Explore the workspace
              </a>
              <p>
                Interface milestone
                <span>No document is uploaded yet</span>
              </p>
            </div>
          </div>

          <div className="principle-list" aria-label="Product principles">
            {principles.map((principle) => (
              <article key={principle.number}>
                <span>{principle.number}</span>
                <div>
                  <h2>{principle.title}</h2>
                  <p>{principle.body}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="workspace" className="workspace-section" aria-labelledby="workspace-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Typed interface exercise</p>
            <h2 id="workspace-title">The document workspace</h2>
          </div>
          <p>
            This first web slice models the states the real API will return. It
            does not upload files or call a model yet.
          </p>
        </div>

        <StudyWorkspacePreview />
      </section>
    </main>
  );
}
