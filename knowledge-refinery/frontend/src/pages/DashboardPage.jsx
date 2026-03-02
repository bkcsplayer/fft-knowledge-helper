import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Activity, CheckCircle, Clock, XCircle, Database, Hash } from 'lucide-react';
import { pipeline, stats } from '../api/client';

const DashboardPage = () => {
    const [searchParams] = useSearchParams();
    const taskId = searchParams.get('taskId');

    const [taskStatus, setTaskStatus] = useState(null);
    const [globalStats, setGlobalStats] = useState(null);

    useEffect(() => {
        // Fetch Global Stats
        stats.get().then(res => setGlobalStats(res.data)).catch(console.error);

        // Polling Task Status
        if (!taskId) return;

        const interval = setInterval(async () => {
            try {
                const res = await pipeline.getStatus(taskId);
                setTaskStatus(res.data);
                if (res.data.status === 'completed' || res.data.status === 'failed') {
                    clearInterval(interval);
                }
            } catch (e) {
                clearInterval(interval);
            }
        }, 2000);

        return () => clearInterval(interval);
    }, [taskId]);

    const renderStageIcon = (status) => {
        switch (status) {
            case 'completed': return <CheckCircle className="w-5 h-5 text-green-500" />;
            case 'running': return <Activity className="w-5 h-5 text-blue-500 animate-pulse" />;
            case 'failed': return <XCircle className="w-5 h-5 text-red-500" />;
            case 'skipped': return <CheckCircle className="w-5 h-5 text-gray-300" />;
            default: return <Clock className="w-5 h-5 text-gray-400" />;
        }
    };

    return (
        <div className="max-w-6xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold mb-4">Dashboard</h1>

            {globalStats && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
                        <h3 className="text-sm font-medium text-gray-500">Total Entries</h3>
                        <p className="mt-2 text-3xl font-bold text-gray-900">{globalStats.total_entries}</p>
                    </div>
                    <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
                        <h3 className="text-sm font-medium text-gray-500">Total API Cost</h3>
                        <p className="mt-2 text-3xl font-bold text-gray-900">${globalStats.total_cost_usd.toFixed(4)}</p>
                    </div>
                    <div className="bg-white p-4 rounded-lg shadow border border-gray-200 col-span-2">
                        <h3 className="text-sm font-medium text-gray-500">Top Tags</h3>
                        <div className="mt-2 flex flex-wrap gap-2">
                            {globalStats.top_tags.map(t => (
                                <span key={t.name} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                                    {t.name} ({t.count})
                                </span>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {taskId && (
                <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                    <h2 className="text-lg font-medium mb-4">Pipeline Status: {taskStatus?.status || 'Loading...'}</h2>

                    {taskStatus && (
                        <div className="space-y-4">
                            {Object.entries(taskStatus.stages).map(([stageName, stageData]) => (
                                <div key={stageName} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                                    <div className="flex items-center gap-3">
                                        {renderStageIcon(stageData.status)}
                                        <span className="font-medium capitalize text-gray-700">{stageName.replace('_', ' ')}</span>
                                    </div>
                                    <div className="flex items-center gap-4 text-sm text-gray-500">
                                        {stageData.duration_ms && <span>{(stageData.duration_ms / 1000).toFixed(1)}s</span>}
                                        {stageData.cost_usd && <span>${stageData.cost_usd.toFixed(4)}</span>}
                                        <span className="w-20 text-right capitalize">{stageData.status}</span>
                                    </div>
                                </div>
                            ))}

                            <div className="flex justify-between items-center pt-4 border-t border-gray-200">
                                <span className="text-sm font-medium text-gray-500">Total Cost: ${taskStatus.total_cost_usd.toFixed(4)}</span>
                                {taskStatus.status === 'completed' && (
                                    <a href={`/entries/${taskStatus.entry_id}`} className="text-primary-600 hover:text-primary-800 text-sm font-medium">View Entry &rarr;</a>
                                )}
                                {taskStatus.status === 'failed' && (
                                    <span className="text-red-500 text-sm">{taskStatus.error || "Execution Failed"}</span>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {!taskId && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                    <div className="bg-gradient-to-br from-indigo-50 to-white p-6 rounded-xl border border-indigo-100 shadow-sm">
                        <div className="w-12 h-12 bg-indigo-100 text-indigo-600 rounded-lg flex items-center justify-center mb-4">
                            <Database className="w-6 h-6" />
                        </div>
                        <h3 className="text-lg font-bold text-gray-900 mb-2">The Knowledge Vault</h3>
                        <p className="text-gray-600 text-sm leading-relaxed">
                            The Vault is where all your processed information lives. When you upload raw text or screenshots, our AI pipeline distills the core facts, verifies them against official sources, and generates a structured Markdown report. You can manage, search, and delete your entries here.
                        </p>
                    </div>

                    <div className="bg-gradient-to-br from-purple-50 to-white p-6 rounded-xl border border-purple-100 shadow-sm">
                        <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-lg flex items-center justify-center mb-4">
                            <Hash className="w-6 h-6" />
                        </div>
                        <h3 className="text-lg font-bold text-gray-900 mb-2">Automated Tags</h3>
                        <p className="text-gray-600 text-sm leading-relaxed">
                            As documents are analyzed, the AI automatically assigns semantic Tags to them (like `React`, `System Design`, or `Bug Fix`). Tags help you organize your Vault. You can view, edit their colors, or delete unused tags in the Tags side menu.
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DashboardPage;
