import { useEffect, useState } from "react";
import axios from "axios";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { User, Edit3, Save, Upload } from "lucide-react";
import { toast } from "sonner";

const Profile = () => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);
  const [profilePic, setProfilePic] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const token = localStorage.getItem("token");
        if (!token) {
          setError("No authentication token found. Please log in.");
          setLoading(false);
          return;
        }

        const response = await axios.get("http://localhost:5000/profile", {
          headers: { Authorization: `Bearer ${token}` },
        });

        setProfile(response.data);
      } catch (err) {
        setError("Failed to load profile. Please try again.");
        console.error("Profile Fetch Error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  const handleSave = async () => {
    try {
      const token = localStorage.getItem("token");
      await axios.put("http://localhost:5000/profile", profile, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success("Profile updated successfully!");
      setEditing(false);
    } catch (err) {
      toast.error("Failed to update profile. Try again later.");
      console.error("Update Error:", err);
    }
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => setProfilePic(reader.result);
      reader.readAsDataURL(file);
    }
  };

  if (loading)
    return <div className="text-center py-10">Loading profile...</div>;
  if (error)
    return <div className="text-center py-10 text-red-500">{error}</div>;
  if (!profile)
    return <div className="text-center py-10">No profile data available.</div>;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          Profile Settings
        </h1>

        <Card className="p-6 mb-8">
          <div className="flex items-center gap-6 mb-6">
            <div className="relative w-24 h-24 rounded-full bg-gray-200 flex items-center justify-center overflow-hidden">
              {profilePic ? (
                <img
                  src={profilePic}
                  alt="Profile"
                  className="w-full h-full object-cover"
                />
              ) : (
                <User className="h-12 w-12 text-gray-400" />
              )}
              <label className="absolute bottom-0 right-0 bg-white p-1 rounded-full cursor-pointer shadow">
                <Upload className="h-4 w-4 text-gray-600" />
                <input
                  type="file"
                  className="hidden"
                  onChange={handleFileChange}
                />
              </label>
            </div>
            <div>
              <h2 className="text-2xl font-semibold">
                {editing ? (
                  <input
                    type="text"
                    className="border p-2 rounded-lg"
                    value={profile.name}
                    onChange={(e) =>
                      setProfile({ ...profile, name: e.target.value })
                    }
                  />
                ) : (
                  profile.name || "No Name"
                )}
              </h2>
              <p className="text-gray-500">Student</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700">Email</label>
              <input
                type="email"
                className="mt-1 w-full p-2 border border-gray-200 rounded-lg"
                value={profile.email || ""}
                disabled
              />
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">
                Learning Pace
              </label>
              <select
                className="mt-1 w-full p-2 border border-gray-200 rounded-lg"
                value={profile.preferences?.pace || "Moderate"}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    preferences: {
                      ...(profile.preferences || {}),
                      pace: e.target.value,
                    },
                  })
                }
              >
                <option>Fast</option>
                <option>Moderate</option>
                <option>Slow</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">
                Content Format
              </label>
              <select
                className="mt-1 w-full p-2 border border-gray-200 rounded-lg"
                value={profile.preferences?.content_format || "Video"}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    preferences: {
                      ...(profile.preferences || {}),
                      content_format: e.target.value,
                    },
                  })
                }
              >
                <option>Video</option>
                <option>Text</option>
                <option>Interactive</option>
              </select>
            </div>
          </div>
        </Card>

        <div className="mt-8 flex justify-end space-x-4">
          {editing ? (
            <>
              <Button variant="outline" onClick={() => setEditing(false)}>
                Cancel
              </Button>
              <Button onClick={handleSave}>
                <Save className="h-4 w-4 mr-2" />
                Save Changes
              </Button>
            </>
          ) : (
            <Button onClick={() => setEditing(true)}>
              <Edit3 className="h-4 w-4 mr-2" />
              Edit Profile
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Profile;
