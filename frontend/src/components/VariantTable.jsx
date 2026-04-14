import React from 'react'
import '../styles/components.css'

function VariantTable({ variants }) {
  if (!variants || variants.length === 0) {
    return <p className="no-variants">No variants detected</p>
  }

  return (
    <div className="variant-table-container">
      <table className="variant-table">
        <thead>
          <tr>
            <th>RS ID</th>
            <th>Gene</th>
            <th>Consequence</th>
          </tr>
        </thead>
        <tbody>
          {variants.map((variant, index) => (
            <tr key={index}>
              <td className="rsid">{variant.rsid || 'Unknown'}</td>
              <td className="gene">{variant.gene || 'Unknown'}</td>
              <td className="consequence">{variant.consequence || 'Unknown'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default VariantTable
