import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

const Layout = ({ onLogout }) => {
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    return (
        <div className="flex h-screen w-full bg-gray-50 overflow-hidden">
            <Sidebar isOpen={isMobileMenuOpen} setIsOpen={setIsMobileMenuOpen} onLogout={onLogout} />
            <div className="flex-1 flex flex-col h-full overflow-hidden w-full">
                <Header onMenuClick={() => setIsMobileMenuOpen(true)} />
                <main className="flex-1 overflow-y-auto w-full p-4 sm:p-6 lg:p-8">
                    <Outlet />
                </main>
            </div>
        </div>
    );
};

export default Layout;
