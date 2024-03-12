import React from 'react';
import { Link } from 'react-router-dom'; // Assuming you're using React Router for navigation

export default function Navbar() {
  return (
    <nav className="navbar navbar-expand-lg bg-body-tertiary">
      <div className="container-fluid">
        <Link className="navbar-brand" to="/">AI Model Hub</Link>
        <ul className="navbar-nav me-auto mb-2 mb-lg-0 flex-row">
          <li className="nav-item">
            <Link className="nav-link active" to="/">Home</Link>
          </li>
          <li className="nav-item">
            <Link className="nav-link" to="/about">About</Link>
          </li>
          <li className="nav-item">
            <Link className="nav-link" to="/contact-us">Contact Us</Link>
          </li>
        </ul>
        <form className="d-flex" role="search">
          <input className="form-control me-2" type="search" placeholder="Search" aria-label="Search" />
          <button className="btn btn-outline-success" type="submit">Search</button>
        </form>
        <Link className="btn btn-primary mx-2" to="/login">Login/Register</Link>
      </div>
    </nav>
  );
}
