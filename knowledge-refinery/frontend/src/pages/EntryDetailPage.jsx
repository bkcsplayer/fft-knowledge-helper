import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { entries } from '../api/client';
import { Calendar, Tag as TagIcon, ExternalLink, ArrowLeft, Trash2, Zap } from 'lucide-react';
import toast from 'react-hot-toast';

const EntryDetailPage = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [entry, setEntry] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        entries.getById(id)
            .then(res => setEntry(res.data))
            .catch(err => {
                toast.error("Entry not found");
                navigate('/entries');
            })
            .finally(() => setLoading(false));
    }, [id, navigate]);

    const handleDelete = async () => {
        if (!window.confirm("Are you sure you want to delete this refined knowledge?")) return;
        try {
            await entries.delete(id);
            toast.success("Entry deleted");
            navigate('/entries');
        } catch (e) {
            toast.error("Failed to delete entry");
        }
    };

    if (loading) return <div className="p-8 text-center text-gray-500">Loading document...</div>;
    if (!entry) return null;

    // Remove frontmatter blocks from markdown string via simple regex
    const contentWithoutFrontmatter = entry.md_content.replace(/^---[\s\S]*?---/, '').trim();

    return (
        <div className="max-w-4xl mx-auto pb-20">
            <button onClick={() => navigate(-1)} className="mb-6 inline-flex items-center text-sm font-medium text-gray-500 hover:text-gray-900 transition">
                <ArrowLeft className="w-4 h-4 mr-1" /> Back
            </button>

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden mb-8">
                <div className="p-6 md:p-8 space-y-6">
                    <div className="flex flex-wrap items-start justify-between gap-4 border-b border-gray-100 pb-6">
                        <div className="space-y-2">
                            <h1 className="text-3xl font-bold text-gray-900 tracking-tight">{entry.title}</h1>
                            <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500 font-medium">
                                <span className="flex items-center gap-1"><Calendar className="w-4 h-4" /> {new Date(entry.created_at).toLocaleDateString()}</span>
                                <span className="uppercase text-primary-600 bg-primary-50 px-2 py-0.5 rounded">{entry.category}</span>
                                {entry.source_url && (
                                    <a href={entry.source_url} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-blue-600 hover:underline">
                                        Source <ExternalLink className="w-3 h-3" />
                                    </a>
                                )}
                            </div>
                        </div>
                        <button onClick={handleDelete} className="text-red-500 hover:bg-red-50 p-2 rounded-md transition">
                            <Trash2 className="w-5 h-5" />
                        </button>
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                        {entry.tags.map(tag => (
                            <span key={tag.id} className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-sm font-medium text-gray-700 bg-gray-100 border border-gray-200">
                                <TagIcon className="w-3 h-3 text-gray-400" /> {tag.name}
                            </span>
                        ))}
                    </div>

                    <div className="bg-blue-50/50 p-5 rounded-lg border border-blue-100 grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                            <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Confidence</p>
                            <p className="mt-1 text-lg text-gray-900 font-bold flex items-center gap-1">
                                {(entry.confidence * 100).toFixed(1)}%
                            </p>
                        </div>
                        <div>
                            <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Actionability</p>
                            <p className="mt-1 text-lg text-gray-900 font-bold capitalize">{entry.actionability}</p>
                        </div>
                        <div>
                            <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Maturity</p>
                            <p className="mt-1 text-lg text-gray-900 font-bold capitalize">{entry.maturity}</p>
                        </div>
                        <div>
                            <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Mode</p>
                            <p className="mt-1 text-lg text-yellow-600 font-bold capitalize flex items-center gap-1">
                                {entry.pipeline_mode === 'quick' && <Zap className="w-4 h-4" />} {entry.pipeline_mode}
                            </p>
                        </div>
                    </div>

                    {entry.review_notes && (
                        <div className="bg-yellow-50 text-yellow-800 p-4 border-l-4 border-yellow-400 text-sm">
                            <span className="font-bold block mb-1">Review Notes:</span>
                            {entry.review_notes}
                        </div>
                    )}
                </div>
            </div>

            <article className="prose prose-blue prose-lg max-w-none bg-white p-8 rounded-xl shadow-sm border border-gray-200">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {contentWithoutFrontmatter}
                </ReactMarkdown>
            </article>
        </div>
    );
};

export default EntryDetailPage;
