import { useState } from 'react'
import { Upload, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'

export function FileUpload() {
  const [file, setFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState('')
  const [downloadUrl, setDownloadUrl] = useState('')
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (!selectedFile) return
    
    // Check file type
    const allowedTypes = ['.txt', '.doc', '.docx']
    const fileExt = selectedFile.name.toLowerCase().slice(selectedFile.name.lastIndexOf('.'))
    if (!allowedTypes.includes(fileExt)) {
      setError('只支持 TXT、DOC、DOCX 格式的文件')
      return
    }
    
    // Check file size (max 10MB)
    if (selectedFile.size > 10 * 1024 * 1024) {
      setError('文件大小不能超过10MB')
      return
    }
    
    setFile(selectedFile)
    setError('')
    setDownloadUrl('')
    setProgress(0)
  }

  const handleUpload = async () => {
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      setIsUploading(true)
      setProgress(0)
      setError('')
      
      const uploadResponse = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/file/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!uploadResponse.ok) {
        throw new Error(await uploadResponse.text())
      }

      const response = await uploadResponse.json()
      
      if (!response.file_id || !response.download_url) {
        throw new Error('服务器响应格式错误')
      }
      
      const { file_id, download_url } = response
      setProgress(20)
      
      // Poll for processing status
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/file/download/${file_id}`)
          
          if (statusResponse.ok) {
            clearInterval(pollInterval)
            setProgress(100)
            setDownloadUrl(download_url)
          } else if (statusResponse.status === 404) {
            setProgress((prev) => Math.min(prev + 5, 90))
          } else {
            throw new Error('文件处理失败')
          }
        } catch (err) {
          clearInterval(pollInterval)
          setError(err instanceof Error ? err.message : '处理失败，请重试')
          setProgress(0)
        }
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
      setProgress(0)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="w-full max-w-md mx-auto space-y-4">
      <div className="flex items-center justify-center w-full">
        <label className="flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-lg cursor-pointer hover:bg-gray-50">
          <div className="flex flex-col items-center justify-center pt-5 pb-6">
            <Upload className="w-10 h-10 mb-3 text-gray-400" />
            <p className="mb-2 text-sm text-gray-500">
              <span className="font-semibold">点击上传</span> 或拖拽文件到此处
            </p>
            <p className="text-xs text-gray-500">支持TXT、DOC、DOCX等文档格式</p>
          </div>
          <input
            type="file"
            className="hidden"
            onChange={handleFileChange}
            accept=".txt,.doc,.docx"
          />
        </label>
      </div>

      {file && (
        <div className="space-y-4">
          <p className="text-sm text-gray-500">已选择: {file.name}</p>
          <Button
            onClick={handleUpload}
            className="w-full"
            disabled={isUploading || !file}
          >
            {isUploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                处理中...
              </>
            ) : (
              '开始处理'
            )}
          </Button>
          {progress > 0 && (
            <div className="space-y-2">
              <Progress value={progress} />
              <p className="text-sm text-gray-500 text-center">
                {progress === 100 ? '处理完成' : '正在处理文件...'}
                {progress > 0 && progress < 100 && ` (${progress}%)`}
              </p>
            </div>
          )}
        </div>
      )}

      {error && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription className="flex items-center">
            <span className="mr-2">⚠️</span>
            {error}
          </AlertDescription>
        </Alert>
      )}

      {downloadUrl && (
        <Alert className="mt-4 bg-green-50 border-green-200">
          <AlertDescription>
            <div className="flex items-center justify-between">
              <span>文件处理完成！</span>
              <a
                href={downloadUrl}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                download
              >
                下载文件
              </a>
            </div>
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}
