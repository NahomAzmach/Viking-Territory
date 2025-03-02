import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import Slider from 'react-slick';
import 'slick-carousel/slick/slick.css';
import 'slick-carousel/slick/slick-theme.css';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
import './PropertyList.css';

// Fix Leaflet default icon issue
let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});
L.Marker.prototype.options.icon = DefaultIcon;

// For AWS EC2 deployment
const API_URL = process.env.NODE_ENV === 'production' 
  ? '' // This will be the root URL of tha EC2 instance
  : 'http://localhost:5000';

function PropertyList() {
  const [properties, setProperties] = useState([]);
  const [filteredProperties, setFilteredProperties] = useState([]);
  const [filters, setFilters] = useState({
    address: '',
    minPrice: '',
    maxPrice: '',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    axios.get(`${API_URL}/properties`)
      .then((response) => {
        // Format properties from DynamoDB response
        const formattedProperties = response.data.map((prop) => ({
          ...prop,
          // Parse coordinates, giving fallbacks for missing values
          latitude: parseFloat(prop.latitude) || 48.7519,
          longitude: parseFloat(prop.longitude) || -122.4787,
          //image URLs parsing
          // DynamoDB might store this either as a string or as a native list so we must beware
          imgUrlsArray: (() => {
            if (prop.source === 'Hammer') {
              if (typeof prop.image_urls === 'string') {
                try {
                  return JSON.parse(prop.image_urls);
                } catch (e) {
                  console.error('Error parsing image URLs:', e);
                  return [];
                }
              } else if (Array.isArray(prop.image_urls)) {
                return prop.image_urls;
              }
            }
            return [];
          })()
        }));
        setProperties(formattedProperties);
        setFilteredProperties(formattedProperties);
        setLoading(false);
      })
      .catch((error) => {
        console.error('Error details:', error.response || error);
        setError('Failed to load properties. Please try again later.');
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    const filtered = properties.filter((property) => {
      const addressMatch = property.address.toLowerCase().includes(filters.address.toLowerCase());
      // Extract numeric price value, handling different formats
      const price = parseInt(property.price?.replace(/[^0-9]/g, ''), 10) || 0;
      const minPriceMatch = !filters.minPrice || price >= parseInt(filters.minPrice, 10);
      const maxPriceMatch = !filters.maxPrice || price <= parseInt(filters.maxPrice, 10);
      return addressMatch && minPriceMatch && maxPriceMatch;
    });
    setFilteredProperties(filtered);
  }, [filters, properties]);

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
  };

  const carouselSettings = {
    dots: true,
    infinite: true,
    speed: 500,
    slidesToShow: 1,
    slidesToScroll: 1,
  };

  if (loading) {
    return <div className="loading">Loading properties...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="property-list-container">
      <h1>Available Properties</h1>

      <div className="filters">
        <input
          type="text"
          name="address"
          placeholder="Filter by Address/Street"
          value={filters.address}
          onChange={handleFilterChange}
        />
        <input
          type="number"
          name="minPrice"
          placeholder="Min Price"
          value={filters.minPrice}
          onChange={handleFilterChange}
        />
        <input
          type="number"
          name="maxPrice"
          placeholder="Max Price"
          value={filters.maxPrice}
          onChange={handleFilterChange}
        />
        <button
          className="reset-button"
          onClick={() => setFilters({ address: '', minPrice: '', maxPrice: '' })}
        >
          Reset Filters
        </button>
      </div>

      <div className="property-list-and-map">
        <div className="property-list">
          {filteredProperties.length === 0 ? (
            <div className="no-properties">No properties match your criteria</div>
          ) : (
            filteredProperties.map((property) => (
              <div className="property-item" key={property.link}>
                {property.source === 'Hammer' && property.imgUrlsArray && property.imgUrlsArray.length > 0 ? (
                  <Slider {...carouselSettings}>
                    {property.imgUrlsArray.map((url, idx) => (
                      <img
                        key={idx}
                        className="property-image"
                        src={url}
                        alt={`Image ${idx + 1} of ${property.address}`}
                        onError={(e) => {
                          e.target.onerror = null;
                          e.target.src = 'https://via.placeholder.com/300x200?text=No+Image';
                        }}
                      />
                    ))}
                  </Slider>
                ) : (
                  <img
                    className="property-image"
                    src={property.image_url || 'https://via.placeholder.com/300x200?text=No+Image'}
                    alt={property.address}
                    onError={(e) => {
                      e.target.onerror = null;
                      e.target.src = 'https://via.placeholder.com/300x200?text=No+Image';
                    }}
                  />
                )}
                <p className="property-price">{property.price}</p>
                <p className="property-address">{property.address}</p>
                {property.link && (
                  <a
                    className="property-link"
                    href={property.link}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    View Listing
                  </a>
                )}
              </div>
            ))
          )}
        </div>

        <div className="map-container">
          <MapContainer
            center={[48.7519, -122.4787]}
            zoom={13}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            {filteredProperties.map(
              (property) =>
                property.latitude &&
                property.longitude && (
                  <Marker
                    key={property.link}
                    position={[property.latitude, property.longitude]}
                  >
                    <Popup>
                      <div className="map-popup">
                        <img
                          src={property.image_url}
                          alt={property.address}
                          className="popup-image"
                          onError={(e) => {
                            e.target.onerror = null;
                            e.target.src = 'https://via.placeholder.com/150x100?text=No+Image';
                          }}
                        />
                        <strong>{property.address}</strong>
                        <p>{property.price}</p>
                        {property.link && (
                          <a
                            href={property.link}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            View Listing
                          </a>
                        )}
                      </div>
                    </Popup>
                  </Marker>
                )
            )}
          </MapContainer>
        </div>
      </div>
    </div>
  );
}

export default PropertyList;
