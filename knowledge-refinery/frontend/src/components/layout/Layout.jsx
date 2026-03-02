import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

const Layout = () => {
    return (
        <div className="flex h-screen w-fullbg-gray-50 overflow-hidden">
            <Sidebar />
            <div className="flex-1 flex flex-col h-full overflow-hidden">
                <Header />
                <main className="flex-1 overflow-y-auto w-full p-6">
                    <Outlet />
                </main>
            </div>
        </div>
    );
};

export default Layout;
