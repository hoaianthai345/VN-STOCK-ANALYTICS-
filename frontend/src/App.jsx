import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import NavigationLayout from './components/NavigationLayout';
import Dashboard from './pages/Dashboard';
import Explorer from './pages/Explorer';
import Advisor from './pages/Advisor';
import Admin from './pages/Admin';

function App() {
  return (
    <Router>
      <NavigationLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/explorer" element={<Explorer />} />
          <Route path="/advisor" element={<Advisor />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </NavigationLayout>
    </Router>
  );
}

export default App;
