import { Link, useLocation } from 'react-router-dom';

const Sidebar = () => {
  const location = useLocation();

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: '📊' },
    { name: 'Policies', path: '/policies', icon: '📄' },
    { name: 'Audits', path: '/audits', icon: '🔍' },
    { name: 'Violations', path: '/violations', icon: '⚠️' },
    { name: 'Settings', path: '/settings', icon: '⚙️' },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <div className="w-64 bg-gray-900 min-h-screen flex flex-col">
      <div className="p-6">
        <h1 className="text-white text-xl font-bold">AI Compliance</h1>
        <p className="text-gray-400 text-sm">Auditor</p>
      </div>
      
      <nav className="flex-1 px-4 space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
              isActive(item.path)
                ? 'bg-gray-800 text-white'
                : 'text-gray-300 hover:bg-gray-800 hover:text-white'
            }`}
          >
            <span className="mr-3 text-lg">{item.icon}</span>
            {item.name}
          </Link>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-800">
        <div className="text-xs text-gray-500 text-center">
          © 2025 AI Compliance Auditor
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
