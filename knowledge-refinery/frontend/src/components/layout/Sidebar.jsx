import { Link, useLocation } from 'react-router-dom';
import { Home, Library, Tags, Settings, BarChart2, X, LogOut } from 'lucide-react';

const Sidebar = ({ isOpen, setIsOpen, onLogout }) => {
    const location = useLocation();

    const navigation = [
        { name: 'Upload', href: '/', icon: Home },
        { name: 'Vault', href: '/entries', icon: Library },
        { name: 'Dashboard', href: '/dashboard', icon: BarChart2 },
        { name: 'Tags', href: '/tags', icon: Tags },
        { name: 'Settings', href: '/settings', icon: Settings },
    ];

    const isActive = (path) => {
        if (path === '/' && location.pathname !== '/') return false;
        return location.pathname.startsWith(path);
    };

    return (
        <>
            {/* Mobile backdrop */}
            {isOpen && (
                <div
                    className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 md:hidden transition-opacity"
                    onClick={() => setIsOpen(false)}
                />
            )}

            {/* Sidebar */}
            <div className={`fixed inset-y-0 left-0 z-50 flex flex-col w-64 bg-white border-r border-gray-200 transform transition-transform duration-300 ease-in-out md:relative md:translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
                <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200">
                    <span className="font-bold text-lg text-primary-600">Knowledge Refinery</span>
                    <button
                        onClick={() => setIsOpen(false)}
                        className="md:hidden p-2 text-gray-400 hover:text-gray-500 focus:outline-none"
                    >
                        <X className="h-5 w-5" />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto py-4 flex flex-col">
                    <nav className="px-4 space-y-1 flex-1">
                        {navigation.map((item) => (
                            <Link
                                key={item.name}
                                to={item.href}
                                onClick={() => setIsOpen(false)}
                                className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${isActive(item.href)
                                    ? 'bg-primary-50 text-primary-600'
                                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                                    }`}
                            >
                                <item.icon
                                    className={`flex-shrink-0 h-5 w-5 mr-3 ${isActive(item.href) ? 'text-primary-600' : 'text-gray-400'
                                        }`}
                                />
                                {item.name}
                            </Link>
                        ))}
                    </nav>

                    <div className="p-4 border-t border-gray-200 mt-auto">
                        <button
                            onClick={() => {
                                setIsOpen(false);
                                onLogout && onLogout();
                            }}
                            className="flex items-center w-full px-3 py-2 text-sm font-medium text-red-600 rounded-md hover:bg-red-50 transition-colors"
                        >
                            <LogOut className="flex-shrink-0 h-5 w-5 mr-3" />
                            Sign Out
                        </button>
                    </div>
                </div>
            </div>
        </>
    );
};

export default Sidebar;
