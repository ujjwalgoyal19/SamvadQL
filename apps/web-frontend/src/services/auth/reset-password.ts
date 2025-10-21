async function resetPassword(
  token: string,
  new_password: string,
): Promise<ApiResponse<any>> {
  try {
    const response = await this.client.post("/api/v1/auth/reset-password", {
      token,
      new_password,
    });
    return { data: response.data, success: true };
  } catch (error: any) {
    return {
      data: undefined as any,
      success: false,
      errors: [error.response?.data?.detail || "Failed to reset password"],
    };
  }
}
