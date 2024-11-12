import React from 'react';
import PropertyList from './components/PropertyList';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Rental Properties</h1>
      </header>
      <PropertyList />
    </div>
  );
}

export default App;
