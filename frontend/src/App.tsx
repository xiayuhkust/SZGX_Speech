import { FileUpload } from './components/FileUpload'

function App() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <h1 className="text-3xl font-bold text-center mb-8">SZGX-Speech 文本处理</h1>
        <FileUpload />
      </div>
    </div>
  )
}

export default App
