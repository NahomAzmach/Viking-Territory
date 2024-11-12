// client/src/components/PropertyList.js
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './PropertyList.css';

function PropertyList() {
  const [properties, setProperties] = useState([]);

  useEffect(() => {
    axios.get('http://localhost:5000/properties')
      .then(response => setProperties(response.data))
      .catch(error => console.error('Error fetching properties:', error));
  }, []);

  return (
    <div>
      <h1>Available Properties</h1>
      <div className="property-list">
        {properties.map((property) => (
          <div className="property-item" key={property.id}>
            <img className="property-image" src={property.image_url} alt={property.title} />
            <div className="property-details">
              <h2 className="property-title">{property.title}</h2>
              <p className="property-price">{property.price}</p>
              <p className="property-address">{property.address}</p>
              <a className="property-link" href={property.link} target="_blank" rel="noopener noreferrer">
                View Listing
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default PropertyList;
