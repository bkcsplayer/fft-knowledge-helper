import { Bell, Search } from 'lucide-react';

const Header = () => {
    return (
        <header className="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-6">
            <div className="flex items-center flex-1">
                <div className="max-w-md w-full relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Search className="h-5 w-5 text-gray-400" />
                    </div>
                    <input
                        type="text"
                        className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-gray-50 placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                        placeholder="Search knowledge..."
                    />
                </div>
            </div>
            <div className="flex items-center">
                <button className="p-2 text-gray-400 hover:text-gray-500 focus:outline-none">
                    <span className="sr-only">View notifications</span>
                    <Bell className="h-6 w-6" />
                </button>
                <div className="ml-4 flex items-center gap-2">
                    <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-bold">
                        U
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;
