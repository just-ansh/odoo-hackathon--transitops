import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { register } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Truck } from "lucide-react";
import { toast } from "sonner";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("Fleet Manager");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await register(email, password, role);
      toast.success("Account created successfully! Please log in.");
      navigate("/login");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Registration failed");
      toast.error(err.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-950">
      <div className="w-full max-w-md space-y-4">
        <div className="flex flex-col items-center gap-2 text-center">
          <div className="grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-xl shadow-indigo-500/20">
            <Truck className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Create your Account</h1>
          <p className="text-sm text-slate-500">
            Select a TransitOps role to test platform access rights
          </p>
        </div>

        <Card className="border-slate-200/70 dark:border-slate-800">
          <CardHeader>
            <CardTitle>Register</CardTitle>
            <CardDescription>
              Create a new user credentials to test RBAC accessibility.
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {error && (
                <div className="rounded-lg bg-rose-50 p-3 text-xs font-medium text-rose-600 dark:bg-rose-950/20 dark:text-rose-400">
                  {error}
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Min. 6 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="role">Assigned Role</Label>
                <Select value={role} onValueChange={setRole}>
                  <SelectTrigger id="role">
                    <SelectValue placeholder="Select a role" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Fleet Manager">Fleet Manager (Full CRUD)</SelectItem>
                    <SelectItem value="Driver">Driver (Trips Only)</SelectItem>
                    <SelectItem value="Safety Officer">Safety Officer (Maintenance Only)</SelectItem>
                    <SelectItem value="Financial Analyst">Financial Analyst (Expenses/Fuel Only)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
            <CardFooter className="flex flex-col gap-4">
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Creating Account..." : "Register"}
              </Button>
              <div className="text-center text-xs text-slate-500">
                Already have an account?{" "}
                <Link to="/login" className="font-medium text-indigo-600 hover:underline dark:text-indigo-400">
                  Sign in
                </Link>
              </div>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}
