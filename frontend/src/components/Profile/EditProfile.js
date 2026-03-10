import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { API_URL } from '../../constants';
import './EditProfile.css';

const EditProfile = () => {
    const { user, updateProfile, uploadProfilePhoto } = useAuth();
    const navigate = useNavigate();

    const [formData, setFormData] = useState({
        first_name: user?.first_name || '',
        last_name: user?.last_name || '',
        email: user?.email || '',
        phone: user?.phone || '',
    });
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');

    const handleChange = (e) => {
        setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setMessage('');
        setLoading(true);

        try {
            await updateProfile(formData);
            setMessage('Profile updated successfully!');
        } catch (err) {
            setError(err.message || 'Failed to update profile');
        }
        setLoading(false);
    };

    const handlePhotoChange = async (e) => {
        if (e.target.files && e.target.files[0]) {
            try {
                setLoading(true);
                await uploadProfilePhoto(e.target.files[0]);
                setMessage('Profile photo updated successfully!');
            } catch (err) {
                setError(err.message || 'Failed to update photo');
            }
            setLoading(false);
        }
    };



    if (!user) {
        navigate('/login');
        return null;
    }

    return (
        <div className="edit-profile-container">
            <div className="edit-profile-card">
                <h2>Edit Profile</h2>

                {error && <div className="auth-error">{error}</div>}
                {message && <div className="auth-success">{message}</div>}

                <div className="profile-photo-section">
                    <div className="photo-preview-container">
                        {user.profile_photo_id ? (
                            <img src={`${API_URL}/profile-photo/${user.profile_photo_id}`} alt="Profile" className="profile-photo-preview photo-circular" style={{ objectFit: 'cover' }} />
                        ) : user.profile_photo_url ? (
                            <img src={user.profile_photo_url} alt="Profile" className="profile-photo-preview photo-circular" style={{ objectFit: 'cover' }} />
                        ) : (
                            <div className="profile-avatar-large photo-circular">
                                {user.first_name?.charAt(0)?.toUpperCase() || 'U'}
                            </div>
                        )}
                    </div>
                    <label className="auth-btn btn-upload-photo" style={{ width: 'auto', display: 'inline-block', marginTop: '1rem', cursor: 'pointer' }}>
                        Change Photo
                        <input type="file" accept="image/*" onChange={handlePhotoChange} style={{ display: 'none' }} disabled={loading} />
                    </label>
                </div>

                <form onSubmit={handleSubmit}>
                    <div className="form-row">
                        <div className="form-group">
                            <label>First Name</label>
                            <input name="first_name" value={formData.first_name} onChange={handleChange} required />
                        </div>
                        <div className="form-group">
                            <label>Last Name</label>
                            <input name="last_name" value={formData.last_name} onChange={handleChange} required />
                        </div>
                    </div>
                    <div className="form-group">
                        <label>Email</label>
                        <input name="email" type="email" value={formData.email} onChange={handleChange} required />
                    </div>
                    <div className="form-group">
                        <label>Phone</label>
                        <input name="phone" value={formData.phone} onChange={handleChange} />
                    </div>
                    <div className="form-actions">
                        <button type="button" className="btn-cancel" onClick={() => navigate(-1)}>Cancel</button>
                        <button type="submit" className="auth-btn" disabled={loading} style={{ width: 'auto', padding: '0.75rem 2rem' }}>
                            {loading ? <span className="spinner-sm"></span> : 'Save Changes'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default EditProfile;
