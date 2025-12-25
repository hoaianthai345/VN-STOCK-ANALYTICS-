import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Compass, Cpu, Settings, LogOut, TrendingUp } from 'lucide-react';

const SidebarItem = ({ to, icon: Icon, label, active }) => (
    <Link
        to={to}
        className={`flex items-center gap-3 px-4 py-3 rounded-md transition-colors border-l-2 ${active
                ? 'bg-gray-800 border-blue-500 text-blue-400'
                : 'border-transparent text-gray-400 hover:bg-gray-900 hover:text-gray-200'
            }`}
    >
        <Icon size={18} />
        <span className="font-medium text-sm">{label}</span>
    </Link>
);

const NavigationLayout = ({ children }) => {
    const location = useLocation();

    const navItems = [
        { to: '/', icon: LayoutDashboard, label: 'Market Overview' },
        { to: '/explorer', icon: Compass, label: 'Explorer' },
        { to: '/advisor', icon: Cpu, label: 'AI Advisor' },
        { to: '/admin', icon: Settings, label: 'Admin Console' },
    ];

    return (
        <div className="flex min-h-screen bg-gray-950 text-gray-100">
            {/* Sidebar */}
            <div className="w-64 bg-gray-950 border-r border-gray-800 flex flex-col fixed h-full z-20">
                <div className="flex items-center gap-3 px-6 py-6 border-b border-gray-800">
                    <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center font-bold text-white shadow-lg shadow-blue-900/50">
                        <TrendingUp size={18} />
                    </div>
                    <div>
                        <h1 className="text-lg font-bold tracking-tight">VN Advisor</h1>
                        <p className="text-xs text-gray-500 uppercase tracking-wider">Pro Terminal</p>
                    </div>
                </div>

                <nav className="flex-1 space-y-1 p-4">
                    <p className="px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 mt-4">Platform</p>
                    {navItems.map((item) => (
                        <SidebarItem
                            key={item.to}
                            {...item}
                            active={location.pathname === item.to}
                        />
                    ))}
                </nav>

                <div className="p-4 border-t border-gray-800">
                    <button className="flex items-center gap-3 px-4 py-3 text-red-500 hover:bg-red-500/10 rounded-md transition-colors w-full text-sm font-medium">
                        <LogOut size={18} />
                        <span>Disconnect</span>
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 ml-64 bg-gray-950">
                {/* Top Header Bar for Ticker Tape or Breadcrumbs could go here */}
                <header className="h-16 border-b border-gray-800 flex items-center justify-between px-8 bg-gray-950/50 backdrop-blur sticky top-0 z-10">
                    <div className="text-sm breadcrumbs text-gray-400">
                        <span className="text-gray-600">Terminal</span> / <span className="text-white font-medium">{navItems.find(i => i.to === location.pathname)?.label || 'Dashboard'}</span>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="text-xs font-mono text-green-500 animate-pulse">● System Operational</div>
                        <div className="w-8 h-8 rounded-full bg-gray-800 border border-gray-700"></div>
                    </div>
                </header>

                <main className="min-h-[calc(100vh-4rem)]">
                    {children}
                </main>
            </div>
        </div>
    );
};

export default NavigationLayout;
