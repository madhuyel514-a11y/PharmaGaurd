import React from 'react'
import '../styles/components.css'

function RiskBadge({ riskLabel, severity }) {
  const getRiskColor = (label) => {
    // Map risk labels to color CSS classes
    switch (label) {
      case 'Safe':
        return 'risk-green'
      case 'Adjust Dosage':
        return 'risk-yellow'     // Orange/warning color
      case 'Toxic':
        return 'risk-red'        // Red/danger color
      case 'Ineffective':
        return 'risk-orange'     // Dark red/critical color
      default:
        return 'risk-gray'
    }
  }

  const getSeverityLabel = (sev) => {
    return sev ? sev.charAt(0).toUpperCase() + sev.slice(1) : 'Unknown'
  }

  return (
    <div className={`risk-badge ${getRiskColor(riskLabel)}`} title={`Risk: ${riskLabel} (${getSeverityLabel(severity)})`}>
      <div className="risk-label">{riskLabel}</div>
      <div className="risk-severity">{getSeverityLabel(severity)}</div>
    </div>
  )
}

export default RiskBadge
