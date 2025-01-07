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

const API_URL = process.env.NODE_ENV === 'production' 
  ? '' 
  : 'http://localhost:5000';

function PropertyList() {
  const [properties, setProperties] = useState([]);
  const [filteredProperties, setFilteredProperties] = useState([]);
  const [filters, setFilters] = useState({
    address: '',
    minPrice: '',
    maxPrice: '',
  });

  useEffect(() => {
    axios.get(`${API_URL}/properties`)
      .then((response) => {
        const formattedProperties = response.data.map((prop) => ({
          ...prop,
          latitude: parseFloat(prop.latitude) || 48.7519,
          longitude: parseFloat(prop.longitude) || -122.4787,
          imgUrlsArray:
            prop.source === 'Hammer' && prop.img_urls
              ? JSON.parse(prop.img_urls) // Parse JSON string for Hammer properties
              : [],
        }));
        setProperties(formattedProperties);
        setFilteredProperties(formattedProperties);
      })
      .catch((error) => {
        console.error('Error details:', error.response || error);
        alert('Failed to load properties. Please check the console for details.');
      });
  }, []);

  useEffect(() => {
    const filtered = properties.filter((property) => {
      const addressMatch = property.address.toLowerCase().includes(filters.address.toLowerCase());
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
          {filteredProperties.map((property) => (
            <div className="property-item" key={property.id || property.address}>
              {property.source === 'Hammer' && property.imgUrlsArray.length > 0 ? (
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
          ))}
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
                    key={property.id || property.address}
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
