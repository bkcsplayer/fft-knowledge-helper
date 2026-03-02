import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
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
import LoginPage from './pages/LoginPage';

function App() {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const auth = localStorage.getItem('isAuthenticated');
        if (auth === 'true') {
            setIsAuthenticated(true);
        }
        setLoading(false);
    }, []);

    if (loading) {
        return <div className="min-h-screen flex items-center justify-center bg-gray-50">Loading...</div>;
    }

    // Protected Route Wrapper
    const ProtectedRoute = ({ children }) => {
        if (!isAuthenticated) {
            return <Navigate to="/login" replace />;
        }
        return children;
    };
    return (
        <Router>
            <Toaster position="top-right" />
            <Routes>
                <Route path="/login" element={
                    isAuthenticated ? <Navigate to="/" replace /> : <LoginPage onLogin={setIsAuthenticated} />
                } />

                <Route path="/" element={
                    <ProtectedRoute>
                        <Layout onLogout={() => {
                            localStorage.removeItem('isAuthenticated');
                            setIsAuthenticated(false);
                        }} />
                    </ProtectedRoute>
                }>
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
