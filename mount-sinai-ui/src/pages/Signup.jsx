import { useForm } from "react-hook-form";
import { supabase } from "../api/supabaseClient"; 
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  Alert,
  MenuItem,
} from "@mui/material";

function Signup() {
  const { register, handleSubmit } = useForm();
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const navigate = useNavigate();

  const onSubmit = async ({ firstName, lastName, email, password, role }) => {
    setError("");
    setSuccess("");

    if (!firstName || !lastName || !email || !password || !role) {
      setError("All fields are required");
      return;
    }

    try {
      // 1. Sign up with Supabase Auth and set redirect URL for email verification
      const { data, error: signUpError } = await supabase.auth.signUp(
        {
          email,
          password,
          options: {
            emailRedirectTo: "http://localhost:5173/login"
          },
        }
      );

      if (signUpError) throw signUpError;

      // 2. Insert user info into your "users" table
      if (data.user) {
        const { error: dbError } = await supabase.from("users").insert([
          {
            email,
            user_id: data.user.id,
            role,
            first_name: firstName,
            last_name: lastName,
            login_time: new Date(),
          },
        ]);

        if (dbError) throw dbError;
      }

      // 3. Show success message
      setSuccess(
        "Signup successful! Please check your email to verify your account."
      );
      setError("");
    } catch (err) {
      console.error("Signup error:", err);
      setError(err.message || "Something went wrong during signup.");
    }
  };

  return (
    <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
      <Paper elevation={3} sx={{ p: 4, width: 350 }}>
        <Typography variant="h5" color="primary" gutterBottom>
          Mount Sinai Signup
        </Typography>

        {error && <Alert severity="error">{error}</Alert>}
        {success && <Alert severity="success">{success}</Alert>}

        <form onSubmit={handleSubmit(onSubmit)}>
          <TextField
            {...register("firstName")}
            label="First Name"
            fullWidth
            margin="normal"
            required
          />
          <TextField
            {...register("lastName")}
            label="Last Name"
            fullWidth
            margin="normal"
            required
          />
          <TextField
            {...register("email")}
            label="Email"
            type="email"
            fullWidth
            margin="normal"
            required
          />
          <TextField
            {...register("password")}
            label="Password"
            type="password"
            fullWidth
            margin="normal"
            required
          />
          <TextField
            {...register("role")}
            select
            label="Role"
            fullWidth
            margin="normal"
            required
          >
            <MenuItem value="agent">Agent</MenuItem>
            <MenuItem value="admin">Admin</MenuItem>
          </TextField>

          <Button
            type="submit"
            variant="contained"
            color="secondary"
            fullWidth
            sx={{ mt: 2 }}
          >
            Sign Up
          </Button>
        </form>
      </Paper>
    </Box>
  );
}

export default Signup;
