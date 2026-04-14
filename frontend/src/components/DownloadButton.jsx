import React, { useState } from 'react'
import { jsPDF } from 'jspdf'
import '../styles/components.css'

function DownloadButton({ results }) {
  const [copySuccess, setCopySuccess] = useState(false)
  const [pdfGenerating, setPdfGenerating] = useState(false)

  const downloadJSON = () => {
    const dataStr = JSON.stringify(results, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `pharmaguard_analysis_${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const copyToClipboard = async () => {
    try {
      const jsonString = JSON.stringify(results, null, 2)
      await navigator.clipboard.writeText(jsonString)
      setCopySuccess(true)
      setTimeout(() => setCopySuccess(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const downloadPDF = async () => {
    setPdfGenerating(true)
    try {
      if (!results || !Array.isArray(results) || results.length === 0) {
        alert('No analysis results available to export.')
        setPdfGenerating(false)
        return
      }

      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
      })

      const pageWidth = pdf.internal.pageSize.getWidth()
      const pageHeight = pdf.internal.pageSize.getHeight()
      const margin = 15
      const contentWidth = pageWidth - 2 * margin
      let yPosition = margin

      // Define colors for medical style
      const headerColor = [0, 102, 204]    // Blue
      const textDarkColor = [26, 35, 50]   // Dark
      const textGrayColor = [107, 114, 128] // Gray
      const lineColor = [200, 200, 200]    // Light gray

      // Helper function to add a new page if needed (returns updated yPosition)
      const checkPageBreak = (spaceNeeded) => {
        if (yPosition + spaceNeeded > pageHeight - margin) {
          pdf.addPage()
          return margin
        }
        return yPosition
      }

      // Helper function to wrap text
      const splitText = (text, maxWidth) => {
        return pdf.splitTextToSize(String(text || ''), maxWidth)
      }

      // ===== HEADER SECTION =====
      pdf.setFontSize(20)
      pdf.setTextColor(...headerColor)
      pdf.text('PharmaGuard', margin, yPosition)
      pdf.setFontSize(10)
      pdf.setTextColor(...textGrayColor)
      pdf.text('Pharmacogenomics Analysis Report', margin, yPosition + 7)
      yPosition += 15

      // Separator line
      pdf.setDrawColor(...lineColor)
      pdf.line(margin, yPosition, pageWidth - margin, yPosition)
      yPosition += 5

      // Patient Information
      pdf.setFontSize(11)
      pdf.setTextColor(...textDarkColor)
      pdf.text('Patient Information', margin, yPosition)
      yPosition += 6

      pdf.setFontSize(9)
      pdf.setTextColor(...textGrayColor)
      const firstResult = results[0] || {}
      const patientId = firstResult.patient_id || 'N/A'
      pdf.text(`Patient ID: ${patientId}`, margin + 2, yPosition)
      yPosition += 5
      pdf.text(`Report Generated: ${new Date().toLocaleString()}`, margin + 2, yPosition)
      yPosition += 8

      // ===== DRUG ANALYSIS SECTION =====
      results.forEach((result, index) => {
        if (!result || typeof result !== 'object') {
          console.warn(`Skipping invalid result at index ${index}`)
          return
        }

        try {
          // Check for page break before each drug section (leave space for drug card)
          yPosition = checkPageBreak(40)

          // Drug Header
          const drugName = result.drug || 'Unknown Drug'
          pdf.setFontSize(12)
          pdf.setTextColor(...headerColor)
          pdf.setFont(undefined, 'bold')
          pdf.text(`Drug: ${drugName}`, margin, yPosition)
          yPosition += 6

          // Drug details box background
          pdf.setFillColor(245, 247, 250)
          pdf.rect(margin + 1, yPosition - 2, contentWidth - 2, 38, 'F')

          pdf.setFontSize(9)
          pdf.setTextColor(...textDarkColor)
          pdf.setFont(undefined, 'normal')

          // Safely access pharmacogenomic profile
          const profile = result.pharmacogenomic_profile || {}
          const primaryGene = profile.primary_gene || 'N/A'
          const phenotype = profile.phenotype || 'N/A'
          const diplotype = profile.diplotype || 'N/A'

          // Define column positions for consistent field layout
          const labelColumnX = margin + 3
          const valueColumnX = margin + 55  // Enough space for longest label "Confidence Score:"

          // Gene
          pdf.setTextColor(...textDarkColor)
          pdf.setFont(undefined, 'bold')
          pdf.text('Gene:', labelColumnX, yPosition)
          pdf.setFont(undefined, 'normal')
          pdf.text(primaryGene, valueColumnX, yPosition)
          yPosition += 5

          // Phenotype
          pdf.setFont(undefined, 'bold')
          pdf.text('Phenotype:', labelColumnX, yPosition)
          pdf.setFont(undefined, 'normal')
          pdf.text(phenotype, valueColumnX, yPosition)
          yPosition += 5

          // Diplotype
          pdf.setFont(undefined, 'bold')
          pdf.text('Diplotype:', labelColumnX, yPosition)
          pdf.setFont(undefined, 'normal')
          pdf.text(diplotype, valueColumnX, yPosition)
          yPosition += 5

          // Confidence Score
          pdf.setFont(undefined, 'bold')
          pdf.text('Confidence Score:', labelColumnX, yPosition)
          pdf.setFont(undefined, 'normal')
          const riskAssessment = result.risk_assessment || {}
          const confidenceScore = riskAssessment.confidence_score || 0
          const confidencePercent = typeof confidenceScore === 'number' 
            ? (confidenceScore * 100).toFixed(0) 
            : 'N/A'
          pdf.text(`${confidencePercent}%`, valueColumnX, yPosition)
          yPosition += 7

          // Clinical Recommendation Section
          yPosition = checkPageBreak(25)
          pdf.setFontSize(10)
          pdf.setTextColor(...headerColor)
          pdf.setFont(undefined, 'bold')
          pdf.text('Clinical Recommendation', margin, yPosition)
          yPosition += 5

          pdf.setFontSize(9)
          pdf.setFont(undefined, 'normal')
          pdf.setTextColor(...textDarkColor)
          const clinicalRec = result.clinical_recommendation || {}
          const recommendation = clinicalRec.action || 'No recommendation available'
          const wrappedRecommendation = splitText(recommendation, contentWidth - 4)
          
          wrappedRecommendation.forEach((line) => {
            yPosition = checkPageBreak(5)
            pdf.text(line, margin + 2, yPosition)
            yPosition += 5
          })
          yPosition += 3

          // Detected Variants Section
          const variants = profile.detected_variants
          if (Array.isArray(variants) && variants.length > 0) {
            yPosition = checkPageBreak(20)
            pdf.setFontSize(10)
            pdf.setTextColor(...headerColor)
            pdf.setFont(undefined, 'bold')
            pdf.text('Detected Variants', margin, yPosition)
            yPosition += 5

            pdf.setFontSize(8)
            pdf.setFont(undefined, 'normal')
            pdf.setTextColor(...textGrayColor)

            variants.forEach((variant) => {
              if (variant && typeof variant === 'object') {
                yPosition = checkPageBreak(8)
                const rsid = variant.rsid || 'Unknown'
                const gene = variant.gene || 'Unknown'
                const consequence = variant.consequence || 'Unknown'
                const variantText = `\u2022 ${rsid} (${gene}): ${consequence}`
                const wrappedVariant = splitText(variantText, contentWidth - 6)
                
                wrappedVariant.forEach((line) => {
                  pdf.text(line, margin + 3, yPosition)
                  yPosition += 4
                })
              }
            })
            yPosition += 2
          }

          // Separator between drugs
          if (index < results.length - 1) {
            yPosition += 3
            pdf.setDrawColor(...lineColor)
            pdf.line(margin, yPosition, pageWidth - margin, yPosition)
            yPosition += 5
          }
        } catch (drugErr) {
          console.error(`Error processing drug ${index}:`, drugErr)
          // Continue with next drug instead of stopping
        }
      })

      // Footer
      const totalPages = pdf.internal.getNumberOfPages()
      for (let pageNum = 1; pageNum <= totalPages; pageNum++) {
        pdf.setPage(pageNum)
        pdf.setFontSize(8)
        pdf.setTextColor(...textGrayColor)
        pdf.text(
          `Page ${pageNum} of ${totalPages}`,
          pageWidth / 2,
          pageHeight - 8,
          { align: 'center' }
        )
      }

      // Save PDF
      pdf.save('PharmaGuard_Report.pdf')
    } catch (err) {
      console.error('Failed to generate PDF:', err)
      alert('Error generating PDF. Please check the console for details.')
    } finally {
      setPdfGenerating(false)
    }
  }

  return (
    <div className="export-toolbar">
      <button 
        onClick={downloadJSON} 
        className="toolbar-button download-button" 
        title="Download results as JSON"
        aria-label="Download JSON"
      >
        <svg className="button-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="7 10 12 15 17 10"></polyline>
          <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
        <span>JSON</span>
      </button>

      <button
        onClick={downloadPDF}
        disabled={pdfGenerating}
        className={`toolbar-button pdf-button ${pdfGenerating ? 'generating' : ''}`}
        title={pdfGenerating ? 'Generating PDF...' : 'Download results as PDF'}
        aria-label="Download PDF"
      >
        <svg className="button-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          {pdfGenerating ? (
            <circle cx="12" cy="12" r="10" style={{ animation: 'spin 1s linear infinite' }}></circle>
          ) : (
            <>
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="12" y1="13" x2="12" y2="19"></line>
              <line x1="9" y1="16" x2="15" y2="16"></line>
            </>
          )}
        </svg>
        <span>{pdfGenerating ? 'Generating...' : 'PDF'}</span>
      </button>

      <button
        onClick={copyToClipboard}
        className={`toolbar-button copy-button ${copySuccess ? 'success' : ''}`}
        title={copySuccess ? 'Copied to clipboard!' : 'Copy to clipboard'}
        aria-label="Copy to clipboard"
      >
        <svg className="button-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          {copySuccess ? (
            <>
              <polyline points="20 6 9 17 4 12"></polyline>
            </>
          ) : (
            <>
              <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
              <rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>
            </>
          )}
        </svg>
        <span>{copySuccess ? 'Copied!' : 'Copy'}</span>
      </button>
    </div>
  )
}

export default DownloadButton
