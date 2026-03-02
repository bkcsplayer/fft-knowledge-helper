import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Layout
import Layout from './components/layout/Layout';

// Pages
import HomePage from './pages/HomePage';
import EntriesPage from './pages/EntriesPage';
import EntryDetailPage from './pages/EntryDetailPage';
import TagsPage from './pages/TagsPage';
import SettingsPage from './pages/SettingsPage';
import DashboardPage from './pages/DashboardPage';

function App() {
    return (
        <Router>
            <Toaster position="top-right" />
            <Routes>
                <Route path="/" element={<Layout />}>
                    <Route index element={<HomePage />} />
                    <Route path="entries" element={<EntriesPage />} />
                    <Route path="entries/:id" element={<EntryDetailPage />} />
                    <Route path="tags" element={<TagsPage />} />
                    <Route path="settings" element={<SettingsPage />} />
                    <Route path="dashboard" element={<DashboardPage />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Route>
            </Routes>
        </Router>
    );
}

export default App;
