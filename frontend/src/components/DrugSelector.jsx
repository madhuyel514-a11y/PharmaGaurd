import React, { useState } from 'react'
import '../styles/components.css'

function DrugSelector({ onDrugsSelect }) {
  const availableDrugs = [
    'CODEINE',
    'WARFARIN',
    'CLOPIDOGREL',
    'SIMVASTATIN',
    'AZATHIOPRINE',
    'FLUOROURACIL'
  ]

  const [selectedDrugs, setSelectedDrugs] = useState([])

  const handleDrugToggle = (drug) => {
    let updated
    if (selectedDrugs.includes(drug)) {
      updated = selectedDrugs.filter(d => d !== drug)
    } else {
      updated = [...selectedDrugs, drug]
    }
    setSelectedDrugs(updated)
    onDrugsSelect(updated)
  }

  const selectAll = () => {
    setSelectedDrugs(availableDrugs)
    onDrugsSelect(availableDrugs)
  }

  const clearAll = () => {
    setSelectedDrugs([])
    onDrugsSelect([])
  }

  return (
    <div className="drug-selector">
      <div className="drug-controls">
        <button onClick={selectAll} className="control-button">
          Select All
        </button>
        <button onClick={clearAll} className="control-button">
          Clear All
        </button>
      </div>

      <div className="drug-grid">
        {availableDrugs.map((drug) => (
          <label key={drug} className="drug-checkbox">
            <input
              type="checkbox"
              checked={selectedDrugs.includes(drug)}
              onChange={() => handleDrugToggle(drug)}
            />
            <span>{drug}</span>
          </label>
        ))}
      </div>

      <div className="drug-info">
        <p>{selectedDrugs.length} drug(s) selected</p>
      </div>
    </div>
  )
}

export default DrugSelector
