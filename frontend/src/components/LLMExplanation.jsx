import React from 'react'
import '../styles/components.css'

function LLMExplanation({ explanation }) {
  if (!explanation) {
    return <p>No explanation available</p>
  }

  return (
    <div className="llm-explanation">
      <h4>Clinical Explanation (AI-Generated)</h4>

      <div className="explanation-section">
        <h5>Summary</h5>
        <p className="explanation-text">{explanation.summary}</p>
      </div>

      {explanation.biological_mechanism && (
        <div className="explanation-section">
          <h5>Biological Mechanism</h5>
          <p className="explanation-text">{explanation.biological_mechanism}</p>
        </div>
      )}

      {explanation.variant_effects && Object.keys(explanation.variant_effects).length > 0 && (
        <div className="explanation-section">
          <h5>Variant Effects</h5>
          <div className="variant-effects-list">
            {Object.entries(explanation.variant_effects).map(([rsid, effect]) => (
              <div key={rsid} className="variant-effect">
                <code>{rsid}</code>: {effect}
              </div>
            ))}
          </div>
        </div>
      )}

      {explanation.fallback && (
        <p className="fallback-note">{'\u26A0'} Fallback explanation used</p>
      )}
    </div>
  )
}

export default LLMExplanation
