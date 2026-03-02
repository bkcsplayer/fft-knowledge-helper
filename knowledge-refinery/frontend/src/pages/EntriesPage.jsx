import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { entries } from '../api/client';
import { Sparkles, Calendar, Tag as TagIcon, ArrowRight, Library, Trash2 } from 'lucide-react';

const EntriesPage = () => {
    const [data, setData] = useState({ items: [], total: 0 });
    const [loading, setLoading] = useState(true);

    const loadEntries = () => {
        setLoading(true);
        entries.getAll({ page: 1, per_page: 50 })
            .then(res => setData(res.data))
            .catch(console.error)
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        loadEntries();
    }, []);

    const handleDelete = async (e, id) => {
        e.preventDefault();
        e.stopPropagation();
        if (window.confirm("Are you sure you want to delete this knowledge entry?")) {
            try {
                await entries.delete(id);
                loadEntries();
            } catch (err) {
                console.error("Failed to delete entry:", err);
                alert("Failed to delete entry.");
            }
        }
    };

    const getMaturityColor = (level) => {
        const colors = {
            seed: 'bg-gray-100 text-gray-800',
            sprouted: 'bg-green-100 text-green-800',
            mature: 'bg-blue-100 text-blue-800',
            stale: 'bg-yellow-100 text-yellow-800',
            archived: 'bg-red-100 text-red-800'
        };
        return colors[level] || colors.seed;
    };

    if (loading) return <div className="p-8 text-center text-gray-500">Loading knowledge vault...</div>;

    return (
        <div className="max-w-6xl mx-auto space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Knowledge Vault</h1>
                    <p className="mt-1 text-sm text-gray-500">Your refined and structured insights ({data.total} total)</p>
                </div>
                <Link to="/" className="bg-primary-600 text-white px-4 py-2 rounded-md font-medium text-sm hover:bg-primary-700 transition">
                    + New Entry
                </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {data.items.map(entry => (
                    <div key={entry.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow flex flex-col h-full">
                        <div className="flex items-start justify-between mb-3">
                            <span className={`px-2.5 py-1 text-xs font-semibold rounded-full ${getMaturityColor(entry.maturity)} capitalize`}>
                                {entry.maturity}
                            </span>
                            <div className="flex items-center gap-1 text-xs font-medium bg-indigo-50 text-indigo-700 px-2 py-1 rounded-md">
                                <Sparkles className="w-3 h-3" /> {(entry.confidence * 100).toFixed(0)}%
                            </div>
                        </div>

                        <h3 className="text-lg font-bold text-gray-900 mb-2 line-clamp-2">{entry.title}</h3>

                        <div className="flex gap-2 mb-4 text-xs text-gray-500 font-medium">
                            <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {new Date(entry.created_at).toLocaleDateString()}</span>
                            <span className="uppercase text-primary-600">{entry.category}</span>
                        </div>

                        <div className="mt-auto pt-4 border-t border-gray-100 space-y-3">
                            <div className="flex flex-wrap gap-1.5">
                                {entry.tags.map(tag => (
                                    <span key={tag.id} className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium text-gray-600 bg-gray-100">
                                        <TagIcon className="w-3 h-3" /> {tag.name}
                                    </span>
                                ))}
                            </div>

                            <Link to={`/entries/${entry.id}`} className="inline-flex items-center text-sm font-medium text-primary-600 hover:text-primary-800">
                                Read Insight <ArrowRight className="w-4 h-4 ml-1" />
                            </Link>

                            <button onClick={(e) => handleDelete(e, entry.id)} className="ml-auto p-1.5 text-gray-400 hover:text-red-500 rounded hover:bg-red-50 transition-colors" title="Delete Entry">
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {data.items.length === 0 && (
                <div className="text-center py-20 bg-white rounded-lg border border-gray-200 border-dashed">
                    <Library className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900">Vault is empty</h3>
                    <p className="text-gray-500 mt-1">Start by uploading some content to distill.</p>
                </div>
            )}
        </div>
    );
};
export default EntriesPage;
