import { Link, useLocation } from 'react-router-dom';
import { Home, Library, Tags, Settings, BarChart2 } from 'lucide-react';

const Sidebar = () => {
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
        <div className="flex flex-col w-64 border-r border-gray-200 bg-white h-full">
            <div className="flex items-center h-16 px-6 border-b border-gray-200">
                <span className="font-bold text-lg text-primary-600">Knowledge Refinery</span>
            </div>
            <div className="flex-1 overflow-y-auto py-4">
                <nav className="px-4 space-y-1">
                    {navigation.map((item) => (
                        <Link
                            key={item.name}
                            to={item.href}
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
            </div>
        </div>
    );
};

export default Sidebar;
