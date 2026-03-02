import { useEffect, useState } from 'react';
import { tags as tagsApi } from '../api/client';
import toast from 'react-hot-toast';
import { Tag as TagIcon, Trash2, Edit2 } from 'lucide-react';

const TagsPage = () => {
    const [tagsList, setTagsList] = useState([]);
    const [loading, setLoading] = useState(true);

    const [editingId, setEditingId] = useState(null);
    const [editName, setEditName] = useState("");
    const [editColor, setEditColor] = useState("");

    const fetchTags = async () => {
        setLoading(true);
        try {
            const res = await tagsApi.getAll();
            setTagsList(res.data);
        } catch (e) {
            toast.error("Failed to fetch tags");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTags();
    }, []);

    const handleDelete = async (id) => {
        if (!window.confirm("Delete this tag?")) return;
        try {
            await tagsApi.delete(id);
            toast.success("Tag deleted");
            fetchTags();
        } catch (e) {
            toast.error("Failed to delete tag");
        }
    };

    const handleUpdate = async (id) => {
        try {
            await tagsApi.update(id, { name: editName, color: editColor });
            toast.success("Tag updated");
            setEditingId(null);
            fetchTags();
        } catch (e) {
            toast.error("Failed to update tag");
        }
    };

    if (loading) return <div className="p-8 text-center text-gray-500">Loading tags...</div>;

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold text-gray-900">Tags Management</h1>

            <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tag Name</th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Usage Count</th>
                            <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {tagsList.map(tag => (
                            <tr key={tag.id}>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    {editingId === tag.id ? (
                                        <div className="flex gap-2">
                                            <input type="text" value={editName} onChange={(e) => setEditName(e.target.value)} className="border rounded px-2 py-1 text-sm" />
                                            <input type="color" value={editColor} onChange={(e) => setEditColor(e.target.value)} className="w-8 h-8 rounded border" />
                                        </div>
                                    ) : (
                                        <div className="flex items-center">
                                            <TagIcon className="flex-shrink-0 h-5 w-5 text-gray-400 mr-2" />
                                            <span className="text-sm font-medium text-gray-900">{tag.name}</span>
                                        </div>
                                    )}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {tag.usage_count}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    {editingId === tag.id ? (
                                        <div className="flex justify-end gap-2">
                                            <button onClick={() => setEditingId(null)} className="text-gray-500 hover:text-gray-900">Cancel</button>
                                            <button onClick={() => handleUpdate(tag.id)} className="text-primary-600 hover:text-primary-900">Save</button>
                                        </div>
                                    ) : (
                                        <div className="flex justify-end gap-3 text-gray-400">
                                            <button onClick={() => {
                                                setEditingId(tag.id);
                                                setEditName(tag.name);
                                                setEditColor(tag.color);
                                            }} className="hover:text-primary-600"><Edit2 className="w-4 h-4" /></button>
                                            <button onClick={() => handleDelete(tag.id)} className="hover:text-red-600"><Trash2 className="w-4 h-4" /></button>
                                        </div>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {tagsList.length === 0 && (
                    <div className="p-8 text-center text-gray-500">No tags found.</div>
                )}
            </div>
        </div>
    );
};
export default TagsPage;
