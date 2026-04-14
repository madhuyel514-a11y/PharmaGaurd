import React, { useState } from 'react'
import FileUploader from './components/FileUploader'
import DrugSelector from './components/DrugSelector'
import ResultsDisplay from './components/ResultsDisplay'
import './styles/App.css'

function App() {
  const [vcfFile, setVcfFile] = useState(null)
  const [selectedDrugs, setSelectedDrugs] = useState([])
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [patientId, setPatientId] = useState('')
  const [darkMode, setDarkMode] = useState(true)
  const themeIcon = darkMode ? '\u2600\uFE0F' : '\uD83C\uDF19'
  const nextThemeTitle = darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'
  const newAnalysisLabel = '\u2190 New Analysis'
  const copyrightLabel = '\u00A9 2026'

  const handleFileSelect = (file) => {
    setVcfFile(file)
    setError(null)
  }

  const handleDrugsSelect = (drugs) => {
    setSelectedDrugs(drugs)
  }

  const handleAnalyze = async () => {
    if (!vcfFile) {
      setError('Please upload a VCF file')
      return
    }

    if (selectedDrugs.length === 0) {
      setError('Please select at least one drug')
      return
    }

    setLoading(true)
    setError(null)

    try {
      // Use the Vite proxy in local development unless an explicit API URL is configured.
      const API_URL = import.meta.env.VITE_API_URL || ''
      const response = await fetch(`${API_URL}/api/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          vcf_file: await vcfFile.text(),
          drugs: selectedDrugs,
          patient_id: patientId || undefined
        })
      })

      const responseText = await response.text()
      let responseData = null

      if (responseText) {
        try {
          responseData = JSON.parse(responseText)
        } catch {
          if (!response.ok) {
            throw new Error(responseText)
          }

          throw new Error(`Server returned invalid JSON (${response.status})`)
        }
      }

      if (!response.ok) {
        throw new Error(
          responseData?.error ||
          `Analysis failed (${response.status}${response.statusText ? ` ${response.statusText}` : ''})`
        )
      }

      if (!responseData) {
        throw new Error(`Server returned an empty response (${response.status})`)
      }

      setResults(responseData)
    } catch (err) {
      setError(err.message || 'Failed to analyze VCF file')
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setVcfFile(null)
    setSelectedDrugs([])
    setResults(null)
    setError(null)
    setPatientId('')
  }

  return (
    <div className={`app ${darkMode ? 'dark-mode' : 'light-mode'}`}>
      <header className="app-header">
        <div className="header-content">
          <div className="header-title">
            <h1>PharmaGuard</h1>
            <p>Pharmacogenomic Risk Prediction System</p>
          </div>
          <button 
            className="theme-toggle"
            onClick={() => setDarkMode(!darkMode)}
            title={nextThemeTitle}
            aria-label={nextThemeTitle}
          >
            {themeIcon}
          </button>
        </div>
      </header>

      <main className="app-main">
        {!results ? (
          <div className="analysis-panel">
            <div className="input-section">
              <h2>Step 1: Upload VCF File</h2>
              <FileUploader onFileSelect={handleFileSelect} />
              {vcfFile && <p className="selected-file">Selected: {vcfFile.name}</p>}
            </div>

            <div className="input-section">
              <h2>Step 2: Select Drugs</h2>
              <DrugSelector onDrugsSelect={handleDrugsSelect} />
              {selectedDrugs.length > 0 && (
                <p className="selected-drugs">Selected: {selectedDrugs.join(', ')}</p>
              )}
            </div>

            <div className="input-section">
              <h2>Step 3: Optional - Enter Patient ID</h2>
              <input
                type="text"
                placeholder="Enter patient ID (optional)"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                className="patient-id-input"
              />
            </div>

            {error && <div className="error-message">{error}</div>}

            <button
              onClick={handleAnalyze}
              disabled={loading || !vcfFile || selectedDrugs.length === 0}
              className="analyze-button"
            >
              {loading ? 'Analyzing...' : 'Analyze'}
            </button>
          </div>
        ) : (
          <div className="results-section">
            <button onClick={handleReset} className="reset-button">
              {newAnalysisLabel}
            </button>
            <ResultsDisplay results={results} />
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>PharmaGuard {copyrightLabel}</p>
      </footer>
    </div>
  )
}

export default App
