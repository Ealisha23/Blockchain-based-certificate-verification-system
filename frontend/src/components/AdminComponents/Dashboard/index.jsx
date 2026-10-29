import { Box, Button, useTheme } from "@mui/material";
import { tokens } from "../../../theme";
// import { mockTransactions } from "../../data/mockData";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import PeopleOutlinedIcon from "@mui/icons-material/PeopleOutlined";
import SchoolIcon from "@mui/icons-material/School";
import CardMembershipOutlinedIcon from "@mui/icons-material/CardMembershipOutlined";
import VerifiedUserIcon from "@mui/icons-material/VerifiedUser";
import Header from "../../../components/AdminComponents/Header/Header";
// import LineChart from "../../components/LineChart";
// import GeographyChart from "../../components/GeographyChart";
// import BarChart from "../../components/BarChart";
import StatBox from "../../AdminComponents/ProgressCircle/StatBox";
// import ProgressCircle from "../../components/ProgressCircle";
import api from "../../../api/api";
import { useEffect, useState } from "react";

const pct = (ratio) => `${Math.round((ratio || 0) * 100)}%`;

const Dashboard = () => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
  const [statData, setStatData] = useState({});
  const [usersIncreasePercentage, setUsersIncreasePercentage] = useState(0);
  const [schoolIncreasePercentage, setSchoolIncreasePercentage] = useState(0);
  const [certificateIncreasePercentage, setCertificateIncreasePercentage] =
    useState(0);
  const [verifiedCertificatePercentage, setVerifiedCertificatePercentage] =
    useState(0);

  const handleParentageIncrease = (increase, total) => {
    return total ? increase / total : 0;
  };

  useEffect(() => {
    api
      .get("/stats")
      .then((response) => {
        setStatData(response.data);
        setUsersIncreasePercentage(
          handleParentageIncrease(
            response.data.users_increase,
            response.data.users
          )
        );
        setSchoolIncreasePercentage(
          handleParentageIncrease(
            response.data.schools_increase,
            response.data.schools
          )
        );
        setCertificateIncreasePercentage(
          handleParentageIncrease(
            response.data.certificate_increase,
            response.data.certificate
          )
        );
        setVerifiedCertificatePercentage(
          handleParentageIncrease(
            response.data.verified_certificate,
            response.data.certificate
          )
        );
      })
      .catch((error) => {
        console.log(error);
      });

    }, []);

  return (
    <Box m="20px">
      {/* HEADER */}
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <Header title="DASHBOARD" subtitle="Welcome to your dashboard" />

        <Box>
          <Button
            sx={{
              backgroundColor: colors.blueAccent[700],
              color: colors.grey[100],
              fontSize: "14px",
              fontWeight: "bold",
              padding: "10px 20px",
            }}
          >
            <DownloadOutlinedIcon sx={{ mr: "10px" }} />
            Download Reports
          </Button>
        </Box>
      </Box>

      {/* GRID & CHARTS */}
      <Box
        display="grid"
        gridTemplateColumns="repeat(12, 1fr)"
        gridAutoRows="140px"
        gap="20px"
      >
        {/* ROW 1 */}
        <Box
          gridColumn="span 3"
          backgroundColor={colors.primary[400]}
          display="flex"
          alignItems="center"
          justifyContent="center"
        >
          <StatBox
            title={statData.users}
            subtitle="Active Users"
            progress={usersIncreasePercentage ? usersIncreasePercentage : ""}
            increase={pct(usersIncreasePercentage)}
            icon={
              <PeopleOutlinedIcon
                sx={{ color: colors.greenAccent[600], fontSize: "26px" }}
              />
            }
          />
        </Box>
        <Box
          gridColumn="span 3"
          backgroundColor={colors.primary[400]}
          display="flex"
          alignItems="center"
          justifyContent="center"
        >
          <StatBox
            title={statData.schools}
            subtitle="Active Schools"
            progress={schoolIncreasePercentage}
            increase={pct(schoolIncreasePercentage)}
            icon={
              <SchoolIcon
                sx={{ color: colors.greenAccent[600], fontSize: "26px" }}
              />
            }
          />
        </Box>
        <Box
          gridColumn="span 3"
          backgroundColor={colors.primary[400]}
          display="flex"
          alignItems="center"
          justifyContent="center"
        >
          <StatBox
            title={statData.certificate}
            subtitle="Clients Certificates"
            progress={certificateIncreasePercentage}
            increase={pct(certificateIncreasePercentage)}
            icon={
              <CardMembershipOutlinedIcon
                sx={{ color: colors.greenAccent[600], fontSize: "26px" }}
              />
            }
          />
        </Box>
        <Box
          gridColumn="span 3"
          backgroundColor={colors.primary[400]}
          display="flex"
          alignItems="center"
          justifyContent="center"
        >
          <StatBox
            title={statData.verified_certificate}
            subtitle="verified Certificates"
            progress={verifiedCertificatePercentage}
            increase={pct(verifiedCertificatePercentage)}
            icon={
              <VerifiedUserIcon
                sx={{ color: colors.greenAccent[600], fontSize: "26px" }}
              />
            }
          />
        </Box>

        {/* <Box
          gridColumn="span 4"
          gridRow="span 2"
          backgroundColor={colors.primary[400]}
          padding="30px"
        >
          <Typography
            variant="h5"
            fontWeight="600"
            sx={{ marginBottom: "15px" }}
          >
            Geography Based Traffic
          </Typography>
          <Box height="200px">
            <GeographyChart isDashboard={true} />
          </Box>
        </Box> */}
      </Box>
    </Box>
  );
};

export default Dashboard;
