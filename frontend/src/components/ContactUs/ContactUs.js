import React from 'react';

export default function ContactUs() {
  return (
    <div className="container mt-5">
      <h2>Contact Us</h2>
      <div className="card mt-4">
        <div className="card-body">
          <p>If you have any questions or feedback, feel free to reach out to us:</p>
          <ul>
            <li>Email: <a href="mailto:contact@example.com">contact@example.com</a></li>
            <li>Phone: <a href="tel:+1234567890">+1234567890</a></li>
            <li>Address: 123 Main St, City, Country</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
