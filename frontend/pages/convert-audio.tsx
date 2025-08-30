import { useState } from 'react';
import { useRouter } from 'next/router';
import styles from '../styles/ConvertAudio.module.css';

export default function ConvertAudio() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isConverting, setIsConverting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const router = useRouter();

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    if (files.length > 0) {
      // Check if all files are supported audio files
      const supportedFormats = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.wma'];
      const invalidFiles = files.filter(file => {
        const fileExt = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
        return !supportedFormats.includes(fileExt);
      });
      
      if (invalidFiles.length > 0) {
        setError(`Please select only supported audio files. Supported formats: ${supportedFormats.join(', ')}. Invalid files: ${invalidFiles.map(f => f.name).join(', ')}`);
        setSelectedFiles([]);
        return;
      }
      
      setSelectedFiles(files);
      setError(null);
      setSuccess(null);
    }
  };

  const handleConvert = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select at least one file first');
      return;
    }

    setIsConverting(true);
    setError(null);
    setSuccess(null);

    try {
      const formData = new FormData();
      selectedFiles.forEach(file => {
        formData.append('files', file);
      });

      const response = await fetch('http://localhost:5557/convert-audio-to-text', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Conversion failed');
      }

      // Get the filename for download
      const contentDisposition = response.headers.get('content-disposition');
      let filename = selectedFiles.length === 1 ? 'transcribed.md' : 'transcribed_files.zip';
      
      if (contentDisposition) {
        // Try different patterns for filename extraction
        const patterns = [
          /filename="([^"]+)"/,  // filename="example.txt"
          /filename=([^;]+)/,    // filename=example.txt
          /filename\*=UTF-8''([^;]+)/  // filename*=UTF-8''example.txt
        ];
        
        for (const pattern of patterns) {
          const match = contentDisposition.match(pattern);
          if (match) {
            filename = decodeURIComponent(match[1]);
            break;
          }
        }
      }
      
      // If we still don't have a proper filename, create one based on files
      if (filename === 'transcribed.md' || filename === 'transcribed_files.zip') {
        if (selectedFiles.length === 1) {
          const originalName = selectedFiles[0].name;
          const baseName = originalName.replace(/\.(mp3|wav|m4a|flac|ogg|aac|wma)$/i, '');
          filename = `${baseName}.md`;
        } else {
          // Create a zip filename based on the first file or use a generic name
          const firstFileName = selectedFiles[0].name.replace(/\.(mp3|wav|m4a|flac|ogg|aac|wma)$/i, '');
          filename = `${firstFileName}_and_${selectedFiles.length - 1}_more_files.zip`;
        }
      }

      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      const fileText = selectedFiles.length === 1 ? 'file' : 'files';
      setSuccess(`Successfully transcribed and downloaded ${selectedFiles.length} ${fileText} as ${filename}`);
      setSelectedFiles([]);
      
      // Reset file input
      const fileInput = document.getElementById('file-input') as HTMLInputElement;
      if (fileInput) {
        fileInput.value = '';
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Conversion failed');
    } finally {
      setIsConverting(false);
    }
  };

  const handleBackToHome = () => {
    router.push('/');
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <button onClick={handleBackToHome} className={styles.backButton}>
          ← Back to AI Assistant
        </button>
        <h1 className={styles.title}>Convert Audio to Markdown</h1>
        <p className={styles.subtitle}>
          Upload your audio files and convert them to Markdown format using OpenAI Whisper.
        </p>
      </div>

      <div className={styles.uploadSection}>
        <div className={styles.uploadArea}>
          <input
            id="file-input"
            type="file"
            accept=".mp3,.wav,.m4a,.flac,.ogg,.aac,.wma"
            multiple
            onChange={handleFileSelect}
            className={styles.fileInput}
          />
          <label htmlFor="file-input" className={styles.fileLabel}>
            <div className={styles.uploadContent}>
              <div className={styles.uploadIcon}>🎵</div>
              <div className={styles.uploadText}>
                {selectedFiles.length > 0 ? (
                  <>
                    <strong>Selected: {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''}</strong>
                    <span>Click to change files</span>
                  </>
                ) : (
                  <>
                    <strong>Choose audio files</strong>
                    <span>or drag and drop here (multiple files supported)</span>
                  </>
                )}
              </div>
            </div>
          </label>
        </div>

        {selectedFiles.length > 0 && (
          <div className={styles.fileInfo}>
            <div className={styles.fileDetails}>
              {selectedFiles.map((file, index) => (
                <div key={index} className={styles.fileItem}>
                  <span className={styles.fileName}>{file.name}</span>
                  <span className={styles.fileSize}>
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className={styles.error}>
            ❌ {error}
          </div>
        )}

        {success && (
          <div className={styles.success}>
            ✅ {success}
          </div>
        )}

        <button
          onClick={handleConvert}
          disabled={selectedFiles.length === 0 || isConverting}
          className={styles.convertButton}
        >
          {isConverting ? 'Transcribing...' : `Transcribe ${selectedFiles.length > 0 ? selectedFiles.length : ''} file${selectedFiles.length !== 1 ? 's' : ''} to Markdown`}
        </button>
      </div>

      <div className={styles.infoSection}>
        <h2>How it works</h2>
        <div className={styles.steps}>
          <div className={styles.step}>
            <div className={styles.stepNumber}>1</div>
            <div className={styles.stepContent}>
              <h3>Upload Audio File</h3>
              <p>Select your audio file using the upload area above</p>
            </div>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNumber}>2</div>
            <div className={styles.stepContent}>
              <h3>Transcribe with Whisper</h3>
              <p>Click the transcribe button to process your audio</p>
            </div>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNumber}>3</div>
            <div className={styles.stepContent}>
              <h3>Download Markdown</h3>
              <p>Your transcribed Markdown file will be automatically downloaded</p>
            </div>
          </div>
        </div>
        
        <div className={styles.supportedFormats}>
          <h3>Supported Audio Formats</h3>
          <p>MP3, WAV, M4A, FLAC, OGG, AAC, WMA</p>
        </div>
      </div>
    </div>
  );
}
