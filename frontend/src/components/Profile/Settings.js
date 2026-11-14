import { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useUI } from '../../context/UIDialog';
import api from '../../services/api';
import './EditProfile.css';

const MIN_LENGTH = 8;

function Section({ title, description, children, danger }) {
    return (
        <section className={`settings-section${danger ? ' settings-danger' : ''}`}>
            <h3>{title}</h3>
            {description && <p className="settings-desc">{description}</p>}
            {children}
        </section>
    );
}

function ChangePassword() {
    const { changePassword } = useAuth();
    const { notify } = useUI();
    const [form, setForm] = useState({ oldPassword: '', newPassword: '', confirm: '' });
    const [error, setError] = useState('');
    const [busy, setBusy] = useState(false);

    const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

    const submit = async (e) => {
        e.preventDefault();
        setError('');
        if (form.newPassword.length < MIN_LENGTH) return setError(`New password must be at least ${MIN_LENGTH} characters.`);
        if (form.newPassword !== form.confirm) return setError('New passwords do not match.');
        setBusy(true);
        try {
            await changePassword(form.oldPassword, form.newPassword);
            setForm({ oldPassword: '', newPassword: '', confirm: '' });
            notify('Password changed. Other devices have been signed out.', 'success');
        } catch (err) {
            setError(err.message || 'Could not change password');
        }
        setBusy(false);
    };

    return (
        <form className="settings-form" onSubmit={submit}>
            {error && <div className="auth-error" role="alert">{error}</div>}
            <div className="form-group">
                <label htmlFor="cp-old">Current password</label>
                <input id="cp-old" type="password" autoComplete="current-password" value={form.oldPassword} onChange={set('oldPassword')} required />
            </div>
            <div className="settings-row">
                <div className="form-group">
                    <label htmlFor="cp-new">New password</label>
                    <input id="cp-new" type="password" autoComplete="new-password" minLength={MIN_LENGTH} value={form.newPassword} onChange={set('newPassword')} required />
                </div>
                <div className="form-group">
                    <label htmlFor="cp-confirm">Confirm new password</label>
                    <input id="cp-confirm" type="password" autoComplete="new-password" minLength={MIN_LENGTH} value={form.confirm} onChange={set('confirm')} required />
                </div>
            </div>
            <button type="submit" className="auth-btn settings-btn" disabled={busy}>
                {busy ? <span className="spinner-sm"></span> : 'Update password'}
            </button>
        </form>
    );
}

function DataSection() {
    const { exportData } = useAuth();
    const { notify } = useUI();
    const [summary, setSummary] = useState(null);
    const [exporting, setExporting] = useState(false);

    useEffect(() => {
        let active = true;
        api.get('/me/storage', { ttl: 0 }).then((d) => active && setSummary(d)).catch(() => {});
        return () => { active = false; };
    }, []);

    const onExport = async () => {
        setExporting(true);
        try {
            await exportData();
        } catch (err) {
            notify(err.message || 'Export failed', 'error');
        }
        setExporting(false);
    };

    return (
        <>
            {summary ? (
                <div className="settings-stats">
                    <div className="settings-stat"><strong>{summary.datasets}</strong><span>Datasets</span></div>
                    <div className="settings-stat"><strong>{summary.training_sessions}</strong><span>Training runs</span></div>
                    <div className="settings-stat"><strong>{summary.pipelines}</strong><span>Saved pipelines</span></div>
                </div>
            ) : (
                <div className="settings-stats settings-stats-loading" aria-hidden="true" />
            )}
            <div className="settings-actions">
                <button type="button" className="auth-btn outline settings-btn" onClick={onExport} disabled={exporting}>
                    {exporting ? 'Preparing export…' : 'Download my data (JSON)'}
                </button>
                <Link to="/datasets" className="auth-btn outline settings-btn">Manage datasets</Link>
                <Link to="/dashboard" className="auth-btn outline settings-btn">Manage training runs</Link>
            </div>
        </>
    );
}

function DeleteAccount() {
    const { user, deleteAccount } = useAuth();
    const { confirm } = useUI();
    const navigate = useNavigate();
    const isOAuth = !!user?.oauth_provider;
    const [secret, setSecret] = useState('');
    const [error, setError] = useState('');
    const [busy, setBusy] = useState(false);

    const submit = async (e) => {
        e.preventDefault();
        setError('');
        const ok = await confirm({
            title: 'Delete account permanently?',
            message: 'Your datasets, trained models, training history and saved pipelines will be permanently deleted. This cannot be undone.',
            confirmText: 'Delete everything',
            danger: true,
        });
        if (!ok) return;
        setBusy(true);
        try {
            await deleteAccount(isOAuth ? { confirm: secret.trim() } : { password: secret });
            navigate('/');
        } catch (err) {
            setError(err.message || 'Failed to delete account');
            setBusy(false);
        }
    };

    return (
        <form className="settings-form" onSubmit={submit}>
            {error && <div className="auth-error" role="alert">{error}</div>}
            <div className="form-group">
                <label htmlFor="del-secret">
                    {isOAuth ? 'Type DELETE to confirm' : 'Enter your password to confirm'}
                </label>
                <input id="del-secret" type={isOAuth ? 'text' : 'password'}
                    autoComplete={isOAuth ? 'off' : 'current-password'}
                    value={secret} onChange={(e) => setSecret(e.target.value)} required />
            </div>
            <button type="submit" className="auth-btn outline danger settings-btn" disabled={busy || !secret}>
                {busy ? <span className="spinner-sm"></span> : 'Delete account'}
            </button>
        </form>
    );
}

const Settings = () => {
    const { user, logoutAll } = useAuth();
    const { confirm, notify } = useUI();
    const navigate = useNavigate();

    const onLogoutAll = async () => {
        const ok = await confirm({
            title: 'Sign out everywhere?',
            message: 'You will be signed out on every device, including this one.',
            confirmText: 'Sign out everywhere',
        });
        if (!ok) return;
        try {
            await logoutAll();
            navigate('/login');
        } catch (err) {
            notify(err.message || 'Could not sign out other devices', 'error');
        }
    };

    return (
        <div className="edit-profile-container">
            <div className="edit-profile-card settings-card">
                <h2>Settings</h2>

                {user?.oauth_provider ? (
                    <Section title="Password" description={`You sign in with ${user.oauth_provider}. To also sign in with a password, use "Forgot password" on the sign-in page to set one.`} />
                ) : (
                    <Section title="Change password" description="Changing your password signs you out on all other devices.">
                        <ChangePassword />
                    </Section>
                )}

                <Section title="Sessions" description="Lost a device or used a shared computer? Revoke every active session.">
                    <button type="button" className="auth-btn outline settings-btn" onClick={onLogoutAll}>
                        Sign out of all devices
                    </button>
                </Section>

                <Section title="Your data" description="See what you're storing and download a copy of everything we hold about your account.">
                    <DataSection />
                </Section>

                <Section danger title="Delete account" description="Permanently delete your account and all of its data.">
                    <DeleteAccount />
                </Section>
            </div>
        </div>
    );
};

export default Settings;
