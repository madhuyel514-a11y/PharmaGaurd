import React, { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import '../styles/components.css'

function FileUploader({ onFileSelect }) {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0]

      // Validate file extension
      if (!file.name.toLowerCase().endsWith('.vcf')) {
        alert('Please upload a VCF file (.vcf)')
        return
      }

      // Validate file size (5MB max)
      const maxSize = 5 * 1024 * 1024
      if (file.size > maxSize) {
        alert('File size exceeds 5MB limit')
        return
      }

      onFileSelect(file)
    }
  }, [onFileSelect])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.vcf']
    },
    multiple: false
  })

  return (
    <div
      {...getRootProps()}
      className={`file-uploader ${isDragActive ? 'active' : ''}`}
    >
      <input {...getInputProps()} />
      {isDragActive ? (
        <p>Drop the VCF file here...</p>
      ) : (
        <div>
          <p className="upload-text">Drag and drop your VCF file here</p>
          <p className="upload-subtext">or click to select a file</p>
          <p className="upload-info">Max file size: 5MB</p>
        </div>
      )}
    </div>
  )
}

export default FileUploader
