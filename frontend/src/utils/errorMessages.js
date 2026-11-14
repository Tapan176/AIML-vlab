/**
 * Map backend machine error codes (e.g. "invalid_credentials") to messages a
 * person can act on. Unknown codes fall through unchanged so nothing is lost.
 */
const MESSAGES = {
    invalid_credentials: 'Incorrect email or password.',
    account_deactivated: 'This account has been deactivated. Contact support if you think this is a mistake.',
    user_already_exists: 'An account with this email already exists. Try signing in or resetting your password.',
    email_already_in_use: 'That email is already used by another account.',
    invalid_email: 'Please enter a valid email address.',
    invalid_password: 'Please enter a valid password.',
    password_too_short: 'Password must be at least 8 characters.',
    password_too_long: 'Password must be at most 128 characters.',
    terms_not_accepted: 'Please accept the terms to continue.',
    incorrect_old_password: 'Your current password is incorrect.',
    incorrect_password: 'Incorrect password.',
    new_password_same_as_old: 'Your new password must be different from the current one.',
    new_password_same_as_old_password: 'Your new password must be different from the current one.',
    invalid_reset_token: 'This reset link is invalid or has already been used. Request a new one.',
    reset_token_expired: 'This reset link has expired. Request a new one.',
    otp_incorrect: 'That code is incorrect. Please try again.',
    otp_expired: 'That code has expired. Request a new one.',
    otp_not_found: 'No active code. Request a new one.',
    otp_too_many_attempts: 'Too many attempts. Request a new code.',
    invalid_otp: 'That code is invalid. Please try again.',
    otp_cooldown: 'Please wait a moment before requesting another code.',
    confirmation_required: 'Please type DELETE to confirm.',
    unsupported_image_type: 'Please upload a JPG, PNG, WEBP or GIF image.',
    image_too_large: 'Image must be 5 MB or smaller.',
    no_valid_fields_to_update: 'Nothing to update.',
    rate_limited: 'Too many requests. Please slow down and try again shortly.',
    too_many_concurrent_trainings: 'You already have the maximum number of trainings running. Wait for one to finish or cancel it.',
    internal_error: 'Something went wrong on our side. Please try again.',
    missing_first_name: 'First name is required.',
    first_name_too_long: 'First name is too long.',
    last_name_too_long: 'Last name is too long.',
};

export function friendlyError(code) {
    if (!code || typeof code !== 'string') return code;
    return MESSAGES[code] || code;
}

export default friendlyError;
