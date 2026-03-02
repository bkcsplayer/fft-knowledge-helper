import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, Link as LinkIcon, FileText, Zap } from 'lucide-react';
import toast from 'react-hot-toast';
import { entries } from '../api/client';

const HomePage = () => {
    const navigate = useNavigate();
    const [inputType, setInputType] = useState('screenshot'); // screenshot, url, text
    const [pipelineMode, setPipelineMode] = useState('deep'); // quick, deep

    const [url, setUrl] = useState('');
    const [text, setText] = useState('');
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        accept: { 'image/*': ['.jpeg', '.jpg', '.png', '.webp'] },
        maxFiles: 1,
        onDrop: (acceptedFiles) => setFile(acceptedFiles[0]),
    });

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (inputType === 'screenshot' && !file) return toast.error('Please select an image file');
        if (inputType === 'url' && !url) return toast.error('Please enter a URL');
        if (inputType === 'text' && !text) return toast.error('Please enter some text');

        setLoading(true);
        const formData = new FormData();
        formData.append('input_type', inputType);
        formData.append('pipeline_mode', pipelineMode);
        if (inputType === 'screenshot') formData.append('file', file);
        if (inputType === 'url') formData.append('url', url);
        if (inputType === 'text') formData.append('text', text);

        try {
            const resp = await entries.upload(formData);
            toast.success(resp.data.message || 'Pipeline started!');
            navigate(`/dashboard?taskId=${resp.data.task_id}`);
        } catch (err) {
            toast.error('Failed to start pipeline processing');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Refine Knowledge</h1>
                <p className="mt-1 text-sm text-gray-500">Transform scattered information into structured assets.</p>
            </div>

            <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
                <div className="flex border-b border-gray-200">
                    <button onClick={() => setInputType('screenshot')} className={`flex-1 py-4 text-sm font-medium flex items-center justify-center gap-2 ${inputType === 'screenshot' ? 'bg-primary-50 text-primary-700 border-b-2 border-primary-500' : 'text-gray-500 hover:text-gray-700'}`}>
                        <UploadCloud className="w-4 h-4" /> Screenshot
                    </button>
                    <button onClick={() => setInputType('url')} className={`flex-1 py-4 text-sm font-medium flex items-center justify-center gap-2 ${inputType === 'url' ? 'bg-primary-50 text-primary-700 border-b-2 border-primary-500' : 'text-gray-500 hover:text-gray-700'}`}>
                        <LinkIcon className="w-4 h-4" /> URL
                    </button>
                    <button onClick={() => setInputType('text')} className={`flex-1 py-4 text-sm font-medium flex items-center justify-center gap-2 ${inputType === 'text' ? 'bg-primary-50 text-primary-700 border-b-2 border-primary-500' : 'text-gray-500 hover:text-gray-700'}`}>
                        <FileText className="w-4 h-4" /> Text
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-6">
                    {inputType === 'screenshot' && (
                        <div
                            {...getRootProps()}
                            className={`mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-dashed rounded-md cursor-pointer transition-colors ${isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-primary-400'
                                }`}
                        >
                            <div className="space-y-1 text-center">
                                <input {...getInputProps()} />
                                <UploadCloud className="mx-auto h-12 w-12 text-gray-400" />
                                <div className="flex text-sm text-gray-600 justify-center">
                                    <span className="relative rounded-md font-medium text-primary-600 hover:text-primary-500">
                                        {file ? file.name : 'Upload a file or drag and drop'}
                                    </span>
                                </div>
                                <p className="text-xs text-gray-500">PNG, JPG, WEBP up to 10MB</p>
                            </div>
                        </div>
                    )}

                    {inputType === 'url' && (
                        <div>
                            <label htmlFor="url" className="block text-sm font-medium text-gray-700">Content URL</label>
                            <input
                                type="url"
                                id="url"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                                placeholder="https://example.com/article"
                            />
                        </div>
                    )}

                    {inputType === 'text' && (
                        <div>
                            <label htmlFor="text" className="block text-sm font-medium text-gray-700">Raw Text</label>
                            <textarea
                                id="text"
                                rows={6}
                                value={text}
                                onChange={(e) => setText(e.target.value)}
                                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                                placeholder="Paste your content here..."
                            />
                        </div>
                    )}

                    <div className="flex items-center justify-between border-t border-gray-200 pt-6">
                        <div className="flex items-center gap-4">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="radio"
                                    name="pipelineMode"
                                    value="deep"
                                    checked={pipelineMode === 'deep'}
                                    onChange={() => setPipelineMode('deep')}
                                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                                />
                                <span className="text-sm font-medium text-gray-900">Deep Mode <span className="text-gray-500 font-normal">(Full verification)</span></span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="radio"
                                    name="pipelineMode"
                                    value="quick"
                                    checked={pipelineMode === 'quick'}
                                    onChange={() => setPipelineMode('quick')}
                                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                                />
                                <span className="text-sm font-medium text-yellow-600 flex items-center gap-1"><Zap className="w-3 h-3" /> Quick Mode <span className="text-gray-500 font-normal">(Skip verification)</span></span>
                            </label>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className={`inline-flex justify-center py-2 px-6 border border-transparent shadow-sm text-sm font-medium rounded-md text-white ${loading ? 'bg-primary-400 cursor-not-allowed' : 'bg-primary-600 hover:bg-primary-700'}`}
                        >
                            {loading ? 'Processing...' : 'Refine'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default HomePage;
