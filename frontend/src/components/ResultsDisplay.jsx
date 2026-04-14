import React, { useState } from 'react'
import RiskBadge from './RiskBadge'
import VariantTable from './VariantTable'
import LLMExplanation from './LLMExplanation'
import DownloadButton from './DownloadButton'
import '../styles/components.css'

function ResultsDisplay({ results }) {
  const [selectedDrug, setSelectedDrug] = useState(null)
  const closeIcon = '\u2715'
  const successIcon = '\u2713'
  const failureIcon = '\u2717'

  const formatPercentage = (value) => {
    if (typeof value !== 'number' || Number.isNaN(value)) {
      return 'N/A'
    }

    return `${Math.round(value * 100)}%`
  }

  const formatList = (items, fallback = 'Not available') => {
    if (!Array.isArray(items) || items.length === 0) {
      return fallback
    }

    return items.join(', ')
  }

  const getMlRiskClass = (riskLevel) => {
    switch ((riskLevel || '').toLowerCase()) {
      case 'low':
        return 'ml-pill-low'
      case 'moderate':
        return 'ml-pill-moderate'
      case 'high':
        return 'ml-pill-high'
      default:
        return 'ml-pill-neutral'
    }
  }

  if (!results || results.length === 0) {
    return <div className="results-empty">No results available</div>
  }

  const openPanel = (result) => {
    setSelectedDrug(result)
  }

  const closePanel = () => {
    setSelectedDrug(null)
  }

  const selectedResult = selectedDrug
    ? results.find((result) => result.drug === selectedDrug.drug) ?? selectedDrug
    : null
  const aiSummary = selectedResult?.ai_summary

  return (
    <div className="results-display" id="analysis-results">
      <div className="results-header">
        <h2>Analysis Results</h2>
        <DownloadButton results={results} />
      </div>

      <div className="results-list">
        {results.map((result, index) => (
          <div 
            key={index} 
            className="result-card"
            onClick={() => openPanel(result)}
          >
            <div className="result-summary">
              <div className="result-title">
                <h3>{result.drug}</h3>
                {!result.error && (
                  <RiskBadge
                    riskLabel={result.risk_assessment?.risk_label}
                    severity={result.risk_assessment?.severity}
                  />
                )}
              </div>

              {!result.error && (
                <div className="result-meta">
                  <div className="meta-item">
                    <span className="label">Phenotype:</span>
                    <span className="value">{result.pharmacogenomic_profile?.phenotype}</span>
                  </div>
                  <div className="meta-item">
                    <span className="label">Gene:</span>
                    <span className="value">{result.pharmacogenomic_profile?.primary_gene}</span>
                  </div>
                  <div className="meta-item">
                    <span className="label">Confidence:</span>
                    <span className="value">{formatPercentage(result.risk_assessment?.confidence_score)}</span>
                  </div>
                  <div className="meta-item">
                    <span className="label">ML Risk:</span>
                    <span className={`value ml-pill ${getMlRiskClass(result.risk_level)}`}>
                      {result.risk_level || 'N/A'}
                    </span>
                  </div>
                  <div className="meta-item">
                    <span className="label">Risk Score:</span>
                    <span className="value">{formatPercentage(result.risk_score)}</span>
                  </div>
                </div>
              )}

              {result.error && (
                <div className="result-error">
                  <p>{result.error}</p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Dark Overlay */}
      {selectedResult && (
        <div className="panel-overlay" onClick={closePanel} />
      )}

      {/* Side Panel */}
      {selectedResult && !selectedResult.error && (
        <div className="details-panel">
          <div className="panel-header">
            <h2>{selectedResult.drug}</h2>
            <button className="close-button" onClick={closePanel} aria-label="Close details panel">
              {closeIcon}
            </button>
          </div>

          <div className="panel-content">
            <div className="detail-section">
              <h4>Risk Assessment</h4>
              <div className="risk-info">
                <div className="risk-info-item">
                  <span className="label">Risk Level:</span>
                  <RiskBadge
                    riskLabel={selectedResult.risk_assessment?.risk_label}
                    severity={selectedResult.risk_assessment?.severity}
                  />
                </div>
                <div className="risk-info-item">
                  <span className="label">Confidence Score:</span>
                  <span className="value">{formatPercentage(selectedResult.risk_assessment?.confidence_score)}</span>
                </div>
              </div>
            </div>

            <div className="detail-section">
              <h4>ML Risk Analysis</h4>
              <div className="risk-info">
                <div className="risk-info-item">
                  <span className="label">Model Prediction:</span>
                  <span className="value">{selectedResult.ml_prediction || 'N/A'}</span>
                </div>
                <div className="risk-info-item">
                  <span className="label">Risk Level:</span>
                  <span className={`value ml-pill ${getMlRiskClass(selectedResult.risk_level)}`}>
                    {selectedResult.risk_level || 'N/A'}
                  </span>
                </div>
                <div className="risk-info-item">
                  <span className="label">Risk Score:</span>
                  <span className="value">{formatPercentage(selectedResult.risk_score)}</span>
                </div>
                <div className="risk-info-item">
                  <span className="label">Model Confidence:</span>
                  <span className="value">{formatPercentage(selectedResult.confidence)}</span>
                </div>
              </div>
            </div>

            <div className="detail-section">
              <h4>Pharmacogenomic Profile</h4>
              <div className="profile-info">
                <div className="profile-item">
                  <span className="label">Primary Gene:</span>
                  <span className="value">{selectedResult.pharmacogenomic_profile?.primary_gene}</span>
                </div>
                <div className="profile-item">
                  <span className="label">Phenotype:</span>
                  <span className="value">{selectedResult.pharmacogenomic_profile?.phenotype}</span>
                </div>
              </div>
            </div>

            <div className="detail-section">
              <h4>Clinical Recommendation</h4>
              <div className="recommendation-box">
                <p><strong>Action:</strong> {selectedResult.clinical_recommendation?.action}</p>
                <p><strong>Dosing:</strong> {selectedResult.clinical_recommendation?.cpic_guideline}</p>
                <p><strong>Monitoring:</strong> {selectedResult.clinical_recommendation?.monitoring}</p>
              </div>
            </div>

            <div className="detail-section">
              <h4>ML Drug Guidance</h4>
              <div className="recommendation-box">
                <p><strong>Recommendation:</strong> {selectedResult.drug_recommendation || 'No ML recommendation available'}</p>
                <p><strong>Alternative Drugs:</strong> {formatList(selectedResult.alternative_drugs, 'No safer alternatives suggested')}</p>
              </div>
            </div>

            {selectedResult.adr_prediction && (
              <div className="detail-section">
                <h4>Adverse Drug Reaction Prediction</h4>
                <div className="profile-info">
                  <div className="profile-item">
                    <span className="label">ADR Risk:</span>
                    <span className="value">{formatPercentage(selectedResult.adr_prediction?.adr_risk)}</span>
                  </div>
                  <div className="profile-item">
                    <span className="label">Possible Reaction:</span>
                    <span className="value wrap-value">{selectedResult.adr_prediction?.possible_reaction || 'Not available'}</span>
                  </div>
                </div>
              </div>
            )}

            {selectedResult.gene_variants && Object.keys(selectedResult.gene_variants).length > 0 && (
              <div className="detail-section">
                <h4>Gene Variant Snapshot</h4>
                <div className="chip-grid">
                  {Object.entries(selectedResult.gene_variants).map(([gene, isPresent]) => (
                    <span
                      key={gene}
                      className={`data-chip ${Number(isPresent) === 1 ? 'data-chip-active' : 'data-chip-inactive'}`}
                    >
                      {gene}: {Number(isPresent) === 1 ? 'Present' : 'Not Detected'}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {selectedResult.pharmacogenomic_profile?.detected_variants?.length > 0 && (
              <div className="detail-section">
                <h4>Detected Variants</h4>
                <VariantTable variants={selectedResult.pharmacogenomic_profile.detected_variants} />
              </div>
            )}

            {aiSummary && (
              <div className="detail-section">
                <h4>{aiSummary.title || 'AI Summary Report'}</h4>
                <div className="ai-summary-card">
                  <div className="summary-subsection">
                    <h5>Detected Pharmacogenes</h5>
                    {aiSummary.detected_pharmacogenes?.length > 0 ? (
                      <div className="chip-grid">
                        {aiSummary.detected_pharmacogenes.map((gene) => (
                          <span key={gene} className="data-chip data-chip-active">
                            {gene}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="empty-state-text">No tracked pharmacogene variants detected</p>
                    )}
                  </div>

                  <div className="summary-subsection">
                    <h5>Drug Risk Analysis</h5>
                    <div className="summary-metrics-grid">
                      <div className="summary-metric-card">
                        <span>High Risk Drugs</span>
                        <strong>{aiSummary.drug_risk_analysis?.counts?.high ?? 0}</strong>
                      </div>
                      <div className="summary-metric-card">
                        <span>Moderate Risk Drugs</span>
                        <strong>{aiSummary.drug_risk_analysis?.counts?.moderate ?? 0}</strong>
                      </div>
                      <div className="summary-metric-card">
                        <span>Low Risk Drugs</span>
                        <strong>{aiSummary.drug_risk_analysis?.counts?.low ?? 0}</strong>
                      </div>
                    </div>
                  </div>

                  <div className="summary-subsection">
                    <h5>Recommendations</h5>
                    {aiSummary.recommendations?.length > 0 ? (
                      <ul className="summary-list">
                        {aiSummary.recommendations.map((recommendation) => (
                          <li key={recommendation}>{recommendation}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="empty-state-text">No additional AI recommendations available</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {selectedResult.llm_generated_explanation && (
              <div className="detail-section">
                <LLMExplanation explanation={selectedResult.llm_generated_explanation} />
              </div>
            )}

            <div className="detail-section">
              <h4>Quality Metrics</h4>
              <div className="metrics-grid">
                <div className="metric">
                  <span>VCF Parse Success:</span>
                  <strong>{selectedResult.quality_metrics?.vcf_parsing_success ? successIcon : failureIcon}</strong>
                </div>
                <div className="metric">
                  <span>Variant Confidence:</span>
                  <strong>{formatPercentage(selectedResult.quality_metrics?.variant_confidence)}</strong>
                </div>
                <div className="metric">
                  <span>Completeness:</span>
                  <strong>{formatPercentage(selectedResult.quality_metrics?.completeness)}</strong>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="results-timestamp">
        {results[0]?.timestamp && (
          <p>Analysis performed: {new Date(results[0].timestamp).toLocaleString()}</p>
        )}
      </div>
    </div>
  )
}

export default ResultsDisplay
