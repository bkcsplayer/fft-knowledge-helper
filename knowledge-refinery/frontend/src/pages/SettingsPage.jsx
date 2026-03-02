import { useEffect, useState } from 'react';
import { profile as profileApi, config as configApi } from '../api/client';
import toast from 'react-hot-toast';
import { Save } from 'lucide-react';

const SettingsPage = () => {
    const [userProfile, setUserProfile] = useState({ profile_name: '', profile_prompt: '' });
    const [modelsInfo, setModelsInfo] = useState([]);
    const [loading, setLoading] = useState(true);
    const [savingProfile, setSavingProfile] = useState(false);

    useEffect(() => {
        Promise.all([
            profileApi.get().then(res => setUserProfile(res.data)),
            configApi.getModels().then(res => setModelsInfo(res.data.models)),
        ]).catch(err => {
            console.error(err);
            toast.error("Failed to load settings data");
        }).finally(() => setLoading(false));
    }, []);

    const handleSaveProfile = async () => {
        setSavingProfile(true);
        try {
            await profileApi.update({
                profile_name: userProfile.profile_name || 'default',
                profile_prompt: userProfile.profile_prompt
            });
            toast.success("Profile saved successfully");
        } catch (e) {
            toast.error("Failed to save profile");
        } finally {
            setSavingProfile(false);
        }
    };

    const handleModelChange = (id, field, value) => {
        setModelsInfo(prev => prev.map(m => m.id === id ? { ...m, [field]: value } : m));
    };

    const handleSaveModel = async (id) => {
        const model = modelsInfo.find(m => m.id === id);
        try {
            await configApi.updateModel(id, {
                model_id: model.model_id,
                max_tokens: Number(model.max_tokens),
                temperature: Number(model.temperature)
            });
            toast.success(`${model.display_name} saved`);
        } catch (e) {
            toast.error(`Failed to save ${model.display_name}`);
        }
    };

    if (loading) return <div className="p-8 text-center text-gray-500">Loading settings...</div>;

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Settings & Configuration</h1>
                <p className="mt-1 text-sm text-gray-500">Manage your user profile context and AI pipeline configurations.</p>
            </div>

            {/* Profile Section */}
            <section className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <div className="px-6 py-5 border-b border-gray-200">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">User Profile Context</h3>
                    <p className="mt-1 max-w-2xl text-sm text-gray-500">
                        This context is injected into the Stage 3 Deep Analysis prompt. Include your background, goals, and business domains.
                    </p>
                </div>
                <div className="px-6 py-5 bg-gray-50 space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Profile Name</label>
                        <input
                            type="text"
                            disabled
                            value={userProfile.profile_name}
                            onChange={(e) => setUserProfile({ ...userProfile, profile_name: e.target.value })}
                            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-primary-500 focus:border-primary-500 sm:text-sm bg-gray-100 cursor-not-allowed"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Background Prompt</label>
                        <textarea
                            rows={8}
                            value={userProfile.profile_prompt}
                            onChange={(e) => setUserProfile({ ...userProfile, profile_prompt: e.target.value })}
                            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                            placeholder="I am a software engineer..."
                        />
                    </div>
                    <div className="text-right">
                        <button
                            onClick={handleSaveProfile}
                            disabled={savingProfile}
                            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
                        >
                            <Save className="w-4 h-4 mr-2" />
                            {savingProfile ? 'Saving...' : 'Save Profile'}
                        </button>
                    </div>
                </div>
            </section>

            {/* Models Configuration Section */}
            <section className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <div className="px-6 py-5 border-b border-gray-200">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">Pipeline Models (OpenRouter)</h3>
                    <p className="mt-1 max-w-2xl text-sm text-gray-500">
                        Configure the LLM IDs used in each stage of the refinery pipeline.
                    </p>
                </div>
                <div className="divide-y divide-gray-200 bg-gray-50">
                    {modelsInfo.map(model => (
                        <div key={model.id} className="p-6 grid grid-cols-1 gap-y-6 sm:grid-cols-4 sm:gap-x-4 items-end">
                            <div className="sm:col-span-2">
                                <label className="block text-sm font-medium text-gray-700">{model.display_name} <br /><span className="text-xs text-gray-400 font-normal">Stage: {model.stage}</span></label>
                                <input
                                    type="text"
                                    value={model.model_id}
                                    onChange={(e) => handleModelChange(model.id, 'model_id', e.target.value)}
                                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-1.5 px-3 focus:ring-primary-500 focus:border-primary-500 sm:text-sm font-mono"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Max Tokens</label>
                                <input
                                    type="number"
                                    value={model.max_tokens}
                                    onChange={(e) => handleModelChange(model.id, 'max_tokens', e.target.value)}
                                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-1.5 px-3 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                                />
                            </div>
                            <div className="flex gap-2 items-center">
                                <div className="flex-1">
                                    <label className="block text-sm font-medium text-gray-700">Temp</label>
                                    <input
                                        type="number" step="0.1" min="0" max="2"
                                        value={model.temperature}
                                        onChange={(e) => handleModelChange(model.id, 'temperature', e.target.value)}
                                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-1.5 px-3 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                                    />
                                </div>
                                <button onClick={() => handleSaveModel(model.id)} className="mt-6 inline-flex items-center p-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 hover:text-primary-600">
                                    <Save className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </section>
        </div>
    );
};
export default SettingsPage;
