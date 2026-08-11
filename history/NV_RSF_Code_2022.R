#1#
#####################################################################################################
#RSF-Take 3 with updated random points strictly within habitat distribution and 5km of rogue leks
#read in main data frame
###rsf_1###
rsf = read.csv("RSF_Ready_DistributionOnly.csv", header = T) 
str(rsf)
summary(rsf)

###putting aspect values into "bins"
rsf$Direction<-ifelse(rsf$Aspect <= 22.5, "N",
                      
                      ifelse(rsf$Aspect > 22.5 & rsf$Aspect <= 67.5, "NE",
                             
                             ifelse(rsf$Aspect > 67.5 & rsf$Aspect <= 112.5, "E",
                                    
                                    ifelse(rsf$Aspect > 112.5 & rsf$Aspect <= 157.5, "SE",
                                           
                                           ifelse(rsf$Aspect > 157.5 & rsf$Aspect <= 202.5, "S",
                                                  
                                                  ifelse(rsf$Aspect > 202.5 & rsf$Aspect <= 247.5, "SW",
                                                         
                                                         ifelse(rsf$Aspect > 247.5 & rsf$Aspect <= 292.5, "W",
                                                                
                                                                ifelse(rsf$Aspect > 292.5 & rsf$Aspect <= 337.5, "NW",
                                                                       
                                                                       ifelse(rsf$Aspect > 337.5 & rsf$Aspect <= 360, "N",
                                                                              
                                                                              ifelse(rsf$Aspect > 360 ,"N", "NA"))))))))))






#convert to factors
rsf$Use = as.factor(rsf$Use)
rsf$Vegetation = as.factor(rsf$Vegetation)
rsf$Direction = as.factor(rsf$Direction)
str(rsf)
summary(rsf)

#Install and load packages
install.packages("lme4") 
library(lme4) 
install.packages('MuMIn')
library(MuMIn)
install.packages('AICcmodavg')
library(AICcmodavg)
install.packages("plyr") 
library(plyr) 
install.packages("dplyr") 
library(dplyr) 




#Rescale
rsf$scale_Curvature = scale(rsf$Curvature)
rsf$scale_RoadsProximity = scale(rsf$RoadsProximity)
rsf$scale_Elevation = scale(rsf$Elevation)
rsf$scale_Ruggedness = scale(rsf$Ruggedness)
rsf$scale_Slope = scale(rsf$Slope)



#Determine Multicollinearity
cor(rsf[c(6:11)])
plot(rsf[c(6:11)])
cor(rsf[c(15:19)])
#No collinear variables-can include all in one model


#A Priori Models
m1 = glm(Use~scale_RoadsProximity + scale_Curvature + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")
m2 = glm(Use~scale_RoadsProximity + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")
m3 = glm(Use~scale_RoadsProximity + scale_Ruggedness + scale_Slope + Vegetation, data = rsf, family = "binomial")
m4 = glm(Use~scale_RoadsProximity + scale_Ruggedness + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")
m5 = glm(Use~scale_Curvature + scale_Slope + scale_Elevation + Vegetation, data = rsf, family = "binomial")
m6 = glm(Use~scale_RoadsProximity + scale_Slope + Vegetation, data = rsf, family = "binomial")
m7 = glm(Use~scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")
m8 = glm(Use~scale_RoadsProximity + scale_Slope + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")
m9 = glm(Use~scale_RoadsProximity + scale_Curvature + scale_Slope + Vegetation, data = rsf, family = "binomial")
m10 = glm(Use~scale_Slope + scale_Elevation + Vegetation, data = rsf, family = "binomial")
m11 = glm(Use~scale_Ruggedness + scale_Slope + Vegetation, data = rsf, family = "binomial")
m12 = glm(Use~scale_RoadsProximity + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")


model.sel(m1,m2,m3,m4,m5,m6,m7,m8,m9,m10,m11,m12)
summary(m1)

library(sjmisc)
library(sjPlot)
library(sjlabelled)

plot_model(m1)
plot_model(m1, vline.color = "black", sort.est = TRUE)

###Adding an "other" variable in the vegetation data so it can be compared to the other data frames (anything thats less than 10 points)
plyr::count(rsf$Vegetation)


#Combining several vegetation types into one category (taking those cover types that are less than 10 in frequency and adding them to a category called "Other")
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SAF 208: Whitebark Pine"] <- "Other"
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SAF 210: Interior Douglas-Fir"] <- "Other"
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SAF 211: White Fir"] <- "Other"
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SRM 106: Bluegrass Scabland"] <- "Other"
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SRM 107: Western Juniper-Big Sagebrush-Bluebunch Wheatgrass"] <- "Other"



rsf <- within(rsf, Vegetation <- relevel(Vegetation, ref = ))


plyr::count(rsf$Vegetation)

####
##Read in subsets of point data that has been broken into 10 different data frames
###1###
###############
rsf_1 = read.csv("DEMPointsVeg_1.csv", header = TRUE)
str(rsf_1)

###putting aspect values into "bins"
rsf_1$Direction<-ifelse(rsf_1$Aspect <= 22.5, "N",
                        
                        ifelse(rsf_1$Aspect > 22.5 & rsf_1$Aspect <= 67.5, "NE",
                               
                               ifelse(rsf_1$Aspect > 67.5 & rsf_1$Aspect <= 112.5, "E",
                                      
                                      ifelse(rsf_1$Aspect > 112.5 & rsf_1$Aspect <= 157.5, "SE",
                                             
                                             ifelse(rsf_1$Aspect > 157.5 & rsf_1$Aspect <= 202.5, "S",
                                                    
                                                    ifelse(rsf_1$Aspect > 202.5 & rsf_1$Aspect <= 247.5, "SW",
                                                           
                                                           ifelse(rsf_1$Aspect > 247.5 & rsf_1$Aspect <= 292.5, "W",
                                                                  
                                                                  ifelse(rsf_1$Aspect > 292.5 & rsf_1$Aspect <= 337.5, "NW",
                                                                         
                                                                         ifelse(rsf_1$Aspect > 337.5 & rsf_1$Aspect <= 360, "N",
                                                                                
                                                                                ifelse(rsf_1$Aspect > 360 ,"N", "NA"))))))))))





#scale the variables to match headings from model
rsf_1$scale_Curvature = scale(rsf_1$Curvature)
rsf_1$scale_RoadsProximity = scale(rsf_1$EucDistRoads)
rsf_1$scale_Elevation = scale(rsf_1$Elevation)
rsf_1$scale_Ruggedness = scale(rsf_1$Ruggedness)
rsf_1$scale_Slope = scale(rsf_1$Slope)
rsf_1$Vegetation = rsf_1$SAF_SRM

rsf_1$Vegetation = as.factor(rsf_1$Vegetation)
rsf_1$Direction = as.factor(rsf_1$Direction)
str(rsf_1)

plyr::count(rsf_1$Vegetation)


#Combining several vegetation types into one category (taking those cover types that are less than 10 in frequency and adding them to a category called "Other")
levels(rsf_1$Vegetation) [levels(rsf_1$Vegetation)=="LF 100: Recently Disturbed Other - Tree"] <- "Other"
levels(rsf_1$Vegetation) [levels(rsf_1$Vegetation)=="LF 63: Recently Logged - Shrub"] <- "Other"
levels(rsf_1$Vegetation) [levels(rsf_1$Vegetation)=="LF 64: Recently Logged - Tree"] <- "Other"
levels(rsf_1$Vegetation) [levels(rsf_1$Vegetation)=="SAF 247: Jeffrey Pine"] <- "Other"



plyr::count(rsf_1$Vegetation)

#Add predictions column to each data frame
rsf_1$predictions = predict(m1, newdata = rsf_1, type = "response")
summary(rsf_1$predictions)

#create new df with just the coordinates and predictions
rsf_1_predict = select(rsf_1, POINT_X, POINT_Y, predictions)

#write new df to .csv
write.csv(rsf_1_predict, file = "rsf_1_predict.csv")
############################################################################




#2#
#####################################################################################################
##rsf_2##
rsf = read.csv("RSF_Ready_DistributionOnly.csv", header = T) 
str(rsf)
summary(rsf)

###putting aspect values into "bins"
rsf$Direction<-ifelse(rsf$Aspect <= 22.5, "N",
                      
                      ifelse(rsf$Aspect > 22.5 & rsf$Aspect <= 67.5, "NE",
                             
                             ifelse(rsf$Aspect > 67.5 & rsf$Aspect <= 112.5, "E",
                                    
                                    ifelse(rsf$Aspect > 112.5 & rsf$Aspect <= 157.5, "SE",
                                           
                                           ifelse(rsf$Aspect > 157.5 & rsf$Aspect <= 202.5, "S",
                                                  
                                                  ifelse(rsf$Aspect > 202.5 & rsf$Aspect <= 247.5, "SW",
                                                         
                                                         ifelse(rsf$Aspect > 247.5 & rsf$Aspect <= 292.5, "W",
                                                                
                                                                ifelse(rsf$Aspect > 292.5 & rsf$Aspect <= 337.5, "NW",
                                                                       
                                                                       ifelse(rsf$Aspect > 337.5 & rsf$Aspect <= 360, "N",
                                                                              
                                                                              ifelse(rsf$Aspect > 360 ,"N", "NA"))))))))))






#convert to factors
rsf$Use = as.factor(rsf$Use)
rsf$Vegetation = as.factor(rsf$Vegetation)
rsf$Direction = as.factor(rsf$Direction)
str(rsf)
summary(rsf)

#Install and load packages
install.packages("lme4") 
library(lme4) 
install.packages('MuMIn')
library(MuMIn)
install.packages('AICcmodavg')
library(AICcmodavg)
install.packages("plyr") 
library(plyr) 
install.packages("dplyr") 
library(dplyr) 




#Rescale
rsf$scale_Curvature = scale(rsf$Curvature)
rsf$scale_RoadsProximity = scale(rsf$RoadsProximity)
rsf$scale_Elevation = scale(rsf$Elevation)
rsf$scale_Ruggedness = scale(rsf$Ruggedness)
rsf$scale_Slope = scale(rsf$Slope)








###Adding an "other" variable in the vegetation data so it can be compared to the other data frames (anything thats less than 10 points)
plyr::count(rsf$Vegetation)


#Combining several vegetation types into one category (taking those cover types that are less than 10 in frequency and adding them to a category called "Other")
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SAF 208: Whitebark Pine"] <- "Other"
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SRM 106: Bluegrass Scabland"] <- "Other"
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SRM 107: Western Juniper-Big Sagebrush-Bluebunch Wheatgrass"] <- "Other"





plyr::count(rsf$Vegetation)


#A Priori Models
m1 = glm(Use~scale_RoadsProximity + scale_Curvature + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")


####
##Read in subsets of point data that has been broken into 10 different data frames
###2###
rsf_2 = read.csv("DEMPointsVeg_2.csv", header = TRUE)
str(rsf_2)

###putting aspect values into "bins"
rsf_2$Direction<-ifelse(rsf_2$Aspect <= 22.5, "N",
                        
                        ifelse(rsf_2$Aspect > 22.5 & rsf_2$Aspect <= 67.5, "NE",
                               
                               ifelse(rsf_2$Aspect > 67.5 & rsf_2$Aspect <= 112.5, "E",
                                      
                                      ifelse(rsf_2$Aspect > 112.5 & rsf_2$Aspect <= 157.5, "SE",
                                             
                                             ifelse(rsf_2$Aspect > 157.5 & rsf_2$Aspect <= 202.5, "S",
                                                    
                                                    ifelse(rsf_2$Aspect > 202.5 & rsf_2$Aspect <= 247.5, "SW",
                                                           
                                                           ifelse(rsf_2$Aspect > 247.5 & rsf_2$Aspect <= 292.5, "W",
                                                                  
                                                                  ifelse(rsf_2$Aspect > 292.5 & rsf_2$Aspect <= 337.5, "NW",
                                                                         
                                                                         ifelse(rsf_2$Aspect > 337.5 & rsf_2$Aspect <= 360, "N",
                                                                                
                                                                                ifelse(rsf_2$Aspect > 360 ,"N", "NA"))))))))))





#scale the variables to match headings from model
rsf_2$scale_Curvature = scale(rsf_2$Curvature)
rsf_2$scale_RoadsProximity = scale(rsf_2$EucDistRoads)
rsf_2$scale_Elevation = scale(rsf_2$Elevation)
rsf_2$scale_Ruggedness = scale(rsf_2$Ruggedness)
rsf_2$scale_Slope = scale(rsf_2$Slope)
rsf_2$Vegetation = rsf_2$SAF_SRM

rsf_2$Vegetation = as.factor(rsf_2$Vegetation)
rsf_2$Direction = as.factor(rsf_2$Direction)
str(rsf_2)

plyr::count(rsf_2$Vegetation)

#look at main rsf file vegetation types
#Combining several vegetation types into one category (taking those cover types that are less than 10 in frequency and adding them to a category called "Other")
levels(rsf_2$Vegetation) [levels(rsf_2$Vegetation)=="LF 100: Recently Disturbed Other - Tree"] <- "Other"
levels(rsf_2$Vegetation) [levels(rsf_2$Vegetation)=="LF 63: Recently Logged - Shrub"] <- "Other"
levels(rsf_2$Vegetation) [levels(rsf_2$Vegetation)=="LF 64: Recently Logged - Tree"] <- "Other"


plyr::count(rsf_2$Vegetation)

#Add predictions column to each data frame
rsf_2$predictions = predict(m1, newdata = rsf_2, type = "response")
summary(rsf_2$predictions)

#create new df with just the coordinates and predictions
rsf_2_predict = select(rsf_2, POINT_X, POINT_Y, predictions)

#write new df to .csv
write.csv(rsf_2_predict, file = "rsf_2_predict.csv")
############################################################################




#3#
#####################################################################################################
##rsf_3##
rsf = read.csv("RSF_Ready_DistributionOnly.csv", header = T) 
str(rsf)
summary(rsf)

###putting aspect values into "bins"
rsf$Direction<-ifelse(rsf$Aspect <= 22.5, "N",
                      
                      ifelse(rsf$Aspect > 22.5 & rsf$Aspect <= 67.5, "NE",
                             
                             ifelse(rsf$Aspect > 67.5 & rsf$Aspect <= 112.5, "E",
                                    
                                    ifelse(rsf$Aspect > 112.5 & rsf$Aspect <= 157.5, "SE",
                                           
                                           ifelse(rsf$Aspect > 157.5 & rsf$Aspect <= 202.5, "S",
                                                  
                                                  ifelse(rsf$Aspect > 202.5 & rsf$Aspect <= 247.5, "SW",
                                                         
                                                         ifelse(rsf$Aspect > 247.5 & rsf$Aspect <= 292.5, "W",
                                                                
                                                                ifelse(rsf$Aspect > 292.5 & rsf$Aspect <= 337.5, "NW",
                                                                       
                                                                       ifelse(rsf$Aspect > 337.5 & rsf$Aspect <= 360, "N",
                                                                              
                                                                              ifelse(rsf$Aspect > 360 ,"N", "NA"))))))))))






#convert to factors
rsf$Use = as.factor(rsf$Use)
rsf$Vegetation = as.factor(rsf$Vegetation)
rsf$Direction = as.factor(rsf$Direction)
str(rsf)
summary(rsf)

#Install and load packages
install.packages("lme4") 
library(lme4) 
install.packages('MuMIn')
library(MuMIn)
install.packages('AICcmodavg')
library(AICcmodavg)
install.packages("plyr") 
library(plyr) 
install.packages("dplyr") 
library(dplyr) 




#Rescale
rsf$scale_Curvature = scale(rsf$Curvature)
rsf$scale_RoadsProximity = scale(rsf$RoadsProximity)
rsf$scale_Elevation = scale(rsf$Elevation)
rsf$scale_Ruggedness = scale(rsf$Ruggedness)
rsf$scale_Slope = scale(rsf$Slope)








###Adding an "other" variable in the vegetation data so it can be compared to the other data frames (anything thats less than 10 points)
plyr::count(rsf$Vegetation)


#Combining several vegetation types into one category (taking those cover types that are less than 10 in frequency and adding them to a category called "Other")
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SAF 208: Whitebark Pine"] <- "Other"
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SRM 106: Bluegrass Scabland"] <- "Other"
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SRM 107: Western Juniper-Big Sagebrush-Bluebunch Wheatgrass"] <- "Other"





plyr::count(rsf$Vegetation)


#A Priori Models
m1 = glm(Use~scale_RoadsProximity + scale_Curvature + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")


####
##Read in subsets of point data that has been broken into 10 different data frames
###3###
rsf_3 = read.csv("DEMPointsVeg_3_corrected_cleaned.csv", header = TRUE)
str(rsf_3)

###putting aspect values into "bins"
rsf_3$Direction<-ifelse(rsf_3$Aspect <= 22.5, "N",
                        
                        ifelse(rsf_3$Aspect > 22.5 & rsf_3$Aspect <= 67.5, "NE",
                               
                               ifelse(rsf_3$Aspect > 67.5 & rsf_3$Aspect <= 112.5, "E",
                                      
                                      ifelse(rsf_3$Aspect > 112.5 & rsf_3$Aspect <= 157.5, "SE",
                                             
                                             ifelse(rsf_3$Aspect > 157.5 & rsf_3$Aspect <= 202.5, "S",
                                                    
                                                    ifelse(rsf_3$Aspect > 202.5 & rsf_3$Aspect <= 247.5, "SW",
                                                           
                                                           ifelse(rsf_3$Aspect > 247.5 & rsf_3$Aspect <= 292.5, "W",
                                                                  
                                                                  ifelse(rsf_3$Aspect > 292.5 & rsf_3$Aspect <= 337.5, "NW",
                                                                         
                                                                         ifelse(rsf_3$Aspect > 337.5 & rsf_3$Aspect <= 360, "N",
                                                                                
                                                                                ifelse(rsf_3$Aspect > 360 ,"N", "NA"))))))))))





#scale the variables to match headings from model
rsf_3$scale_Curvature = scale(rsf_3$Curvature)
rsf_3$scale_RoadsProximity = scale(rsf_3$EucDistRoads)
rsf_3$scale_Elevation = scale(rsf_3$Elevation)
rsf_3$scale_Ruggedness = scale(rsf_3$Ruggedness)
rsf_3$scale_Slope = scale(rsf_3$Slope)
rsf_3$Vegetation = rsf_3$SAF_SRM

rsf_3$Vegetation = as.factor(rsf_3$Vegetation)
rsf_3$Direction = as.factor(rsf_3$Direction)
str(rsf_3)

plyr::count(rsf_3$Vegetation)

#look at main rsf file vegetation types
#Combining several vegetation types into one category (taking those cover types that are less than 10 in frequency and adding them to a category called "Other")
levels(rsf_3$Vegetation) [levels(rsf_3$Vegetation)=="LF 100: Recently Disturbed Other - Tree"] <- "Other"
levels(rsf_3$Vegetation) [levels(rsf_3$Vegetation)=="LF 11: Water"] <- "Other"
levels(rsf_3$Vegetation) [levels(rsf_3$Vegetation)=="LF 63: Recently Logged - Shrub"] <- "Other"
levels(rsf_3$Vegetation) [levels(rsf_3$Vegetation)=="LF 64: Recently Logged - Tree"] <- "Other"
levels(rsf_3$Vegetation) [levels(rsf_3$Vegetation)=="SAF 237: Interior Ponderosa Pine"] <- "Other"
levels(rsf_3$Vegetation) [levels(rsf_3$Vegetation)=="SRM 413: Gambel oak"] <- "Other"


plyr::count(rsf_3$Vegetation)

#Add predictions column to each data frame
rsf_3$predictions = predict(m1, newdata = rsf_3, type = "response")
summary(rsf_3$predictions)

#create new df with just the coordinates and predictions
rsf_3_predict = select(rsf_3, POINT_X, POINT_Y, predictions)

#write new df to .csv
write.csv(rsf_3_predict, file = "rsf_3_predict.csv")
############################################################################




#4 
#####################################################################################################
##rsf_4##
rsf = read.csv("RSF_Ready_DistributionOnly.csv", header = T) 
str(rsf)
summary(rsf)

###putting aspect values into "bins"
rsf$Direction<-ifelse(rsf$Aspect <= 22.5, "N",
                      
                      ifelse(rsf$Aspect > 22.5 & rsf$Aspect <= 67.5, "NE",
                             
                             ifelse(rsf$Aspect > 67.5 & rsf$Aspect <= 112.5, "E",
                                    
                                    ifelse(rsf$Aspect > 112.5 & rsf$Aspect <= 157.5, "SE",
                                           
                                           ifelse(rsf$Aspect > 157.5 & rsf$Aspect <= 202.5, "S",
                                                  
                                                  ifelse(rsf$Aspect > 202.5 & rsf$Aspect <= 247.5, "SW",
                                                         
                                                         ifelse(rsf$Aspect > 247.5 & rsf$Aspect <= 292.5, "W",
                                                                
                                                                ifelse(rsf$Aspect > 292.5 & rsf$Aspect <= 337.5, "NW",
                                                                       
                                                                       ifelse(rsf$Aspect > 337.5 & rsf$Aspect <= 360, "N",
                                                                              
                                                                              ifelse(rsf$Aspect > 360 ,"N", "NA"))))))))))






#convert to factors
rsf$Use = as.factor(rsf$Use)
rsf$Vegetation = as.factor(rsf$Vegetation)
rsf$Direction = as.factor(rsf$Direction)
str(rsf)
summary(rsf)



#Rescale
rsf$scale_Curvature = scale(rsf$Curvature)
rsf$scale_RoadsProximity = scale(rsf$RoadsProximity)
rsf$scale_Elevation = scale(rsf$Elevation)
rsf$scale_Ruggedness = scale(rsf$Ruggedness)
rsf$scale_Slope = scale(rsf$Slope)


####
##Read in subsets of point data that has been broken into 10 different data frames
###4###
rsf_4 = read.csv("DEMPointsVeg_4_corrected_cleaned.csv", header = TRUE)
str(rsf_4)

###putting aspect values into "bins"
rsf_4$Direction<-ifelse(rsf_4$Aspect <= 22.5, "N",
                        
                        ifelse(rsf_4$Aspect > 22.5 & rsf_4$Aspect <= 67.5, "NE",
                               
                               ifelse(rsf_4$Aspect > 67.5 & rsf_4$Aspect <= 112.5, "E",
                                      
                                      ifelse(rsf_4$Aspect > 112.5 & rsf_4$Aspect <= 157.5, "SE",
                                             
                                             ifelse(rsf_4$Aspect > 157.5 & rsf_4$Aspect <= 202.5, "S",
                                                    
                                                    ifelse(rsf_4$Aspect > 202.5 & rsf_4$Aspect <= 247.5, "SW",
                                                           
                                                           ifelse(rsf_4$Aspect > 247.5 & rsf_4$Aspect <= 292.5, "W",
                                                                  
                                                                  ifelse(rsf_4$Aspect > 292.5 & rsf_4$Aspect <= 337.5, "NW",
                                                                         
                                                                         ifelse(rsf_4$Aspect > 337.5 & rsf_4$Aspect <= 360, "N",
                                                                                
                                                                                ifelse(rsf_4$Aspect > 360 ,"N", "NA"))))))))))





#scale the variables to match headings from model
rsf_4$scale_Curvature = scale(rsf_4$Curvature)
rsf_4$scale_RoadsProximity = scale(rsf_4$EucDistRoads)
rsf_4$scale_Elevation = scale(rsf_4$Elevation)
rsf_4$scale_Ruggedness = scale(rsf_4$Ruggedness)
rsf_4$scale_Slope = scale(rsf_4$Slope)
rsf_4$Vegetation = rsf_4$SAF_SRM

rsf_4$Vegetation = as.factor(rsf_4$Vegetation)
rsf_4$Direction = as.factor(rsf_4$Direction)
str(rsf_4)


###Adding an "other" variable in the vegetation data so it can be compared to the other data frames (anything thats less than 10 points)
#RSF MAIN FILE
plyr::count(rsf$Vegetation)


#Combining several vegetation types into one category (taking those cover types that are less than 10 in frequency and adding them to a category called "Other")
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SAF 208: Whitebark Pine"] <- "Other"
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SRM 106: Bluegrass Scabland"] <- "Other"
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SRM 107: Western Juniper-Big Sagebrush-Bluebunch Wheatgrass"] <- "Other"


plyr::count(rsf$Vegetation)


#A Priori Model to be ran on the updated main file
m1 = glm(Use~scale_RoadsProximity + scale_Curvature + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")

#RSF_#
plyr::count(rsf_4$Vegetation)

#look at main rsf file vegetation types
#Combining several vegetation types into one category (taking those cover types that are less than 10 in frequency and adding them to a category called "Other")
levels(rsf_4$Vegetation) [levels(rsf_4$Vegetation)=="LF 100: Recently Disturbed Other - Tree"] <- "Other"
levels(rsf_4$Vegetation) [levels(rsf_4$Vegetation)=="LF 63: Recently Logged - Shrub"] <- "Other"
levels(rsf_4$Vegetation) [levels(rsf_4$Vegetation)=="LF 64: Recently Logged - Tree"] <- "Other"
levels(rsf_4$Vegetation) [levels(rsf_4$Vegetation)=="SAF 210: Interior Douglas-Fir"] <- "Other"
levels(rsf_4$Vegetation) [levels(rsf_4$Vegetation)=="SAF 211: White Fir"] <- "Other"
levels(rsf_4$Vegetation) [levels(rsf_4$Vegetation)=="SAF 237: Interior Ponderosa Pine"] <- "Other"



plyr::count(rsf_4$Vegetation)

#Add predictions column to each data frame
rsf_4$predictions = predict(m1, newdata = rsf_4, type = "response")
summary(rsf_4$predictions)

#create new df with just the coordinates and predictions
rsf_4_predict = select(rsf_4, POINT_X, POINTY, predictions)

#write new df to .csv
write.csv(rsf_4_predict, file = "rsf_4_predict.csv")
############################################################################




#5#
#####################################################################################################
##rsf_5##
rsf = read.csv("RSF_Ready_DistributionOnly.csv", header = T) 
str(rsf)
summary(rsf)

###putting aspect values into "bins"
rsf$Direction<-ifelse(rsf$Aspect <= 22.5, "N",
                      
                      ifelse(rsf$Aspect > 22.5 & rsf$Aspect <= 67.5, "NE",
                             
                             ifelse(rsf$Aspect > 67.5 & rsf$Aspect <= 112.5, "E",
                                    
                                    ifelse(rsf$Aspect > 112.5 & rsf$Aspect <= 157.5, "SE",
                                           
                                           ifelse(rsf$Aspect > 157.5 & rsf$Aspect <= 202.5, "S",
                                                  
                                                  ifelse(rsf$Aspect > 202.5 & rsf$Aspect <= 247.5, "SW",
                                                         
                                                         ifelse(rsf$Aspect > 247.5 & rsf$Aspect <= 292.5, "W",
                                                                
                                                                ifelse(rsf$Aspect > 292.5 & rsf$Aspect <= 337.5, "NW",
                                                                       
                                                                       ifelse(rsf$Aspect > 337.5 & rsf$Aspect <= 360, "N",
                                                                              
                                                                              ifelse(rsf$Aspect > 360 ,"N", "NA"))))))))))






#convert to factors
rsf$Use = as.factor(rsf$Use)
rsf$Vegetation = as.factor(rsf$Vegetation)
rsf$Direction = as.factor(rsf$Direction)
str(rsf)
summary(rsf)

#Install and load packages
install.packages("lme4") 
library(lme4) 
install.packages('MuMIn')
library(MuMIn)
install.packages('AICcmodavg')
library(AICcmodavg)
install.packages("plyr") 
library(plyr) 
install.packages("dplyr") 
library(dplyr) 




#Rescale
rsf$scale_Curvature = scale(rsf$Curvature)
rsf$scale_RoadsProximity = scale(rsf$RoadsProximity)
rsf$scale_Elevation = scale(rsf$Elevation)
rsf$scale_Ruggedness = scale(rsf$Ruggedness)
rsf$scale_Slope = scale(rsf$Slope)







#*#
###Adding an "other" variable in the vegetation data so it can be compared to the other data frames (anything thats less than 10 points)
plyr::count(rsf$Vegetation)


#Combining several vegetation types into one category (taking those cover types that are less than 10 in frequency and adding them to a category called "Other")
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SAF 208: Whitebark Pine"] <- "Other"





plyr::count(rsf$Vegetation)


#A Priori Models
m1 = glm(Use~scale_RoadsProximity + scale_Curvature + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")


####
##Read in subsets of point data that has been broken into 10 different data frames
###5###
rsf_5 = read.csv("DEMPointsVeg_5_corrected_cleaned.csv", header = TRUE)
str(rsf_5)

###putting aspect values into "bins"
rsf_5$Direction<-ifelse(rsf_5$Aspect <= 22.5, "N",
                        
                        ifelse(rsf_5$Aspect > 22.5 & rsf_5$Aspect <= 67.5, "NE",
                               
                               ifelse(rsf_5$Aspect > 67.5 & rsf_5$Aspect <= 112.5, "E",
                                      
                                      ifelse(rsf_5$Aspect > 112.5 & rsf_5$Aspect <= 157.5, "SE",
                                             
                                             ifelse(rsf_5$Aspect > 157.5 & rsf_5$Aspect <= 202.5, "S",
                                                    
                                                    ifelse(rsf_5$Aspect > 202.5 & rsf_5$Aspect <= 247.5, "SW",
                                                           
                                                           ifelse(rsf_5$Aspect > 247.5 & rsf_5$Aspect <= 292.5, "W",
                                                                  
                                                                  ifelse(rsf_5$Aspect > 292.5 & rsf_5$Aspect <= 337.5, "NW",
                                                                         
                                                                         ifelse(rsf_5$Aspect > 337.5 & rsf_5$Aspect <= 360, "N",
                                                                                
                                                                                ifelse(rsf_5$Aspect > 360 ,"N", "NA"))))))))))





#scale the variables to match headings from model
rsf_5$scale_Curvature = scale(rsf_5$Curvature)
rsf_5$scale_RoadsProximity = scale(rsf_5$EucDistRoads)
rsf_5$scale_Elevation = scale(rsf_5$Elevation)
rsf_5$scale_Ruggedness = scale(rsf_5$Ruggedness)
rsf_5$scale_Slope = scale(rsf_5$Slope)
rsf_5$Vegetation = rsf_5$SAF_SRM

rsf_5$Vegetation = as.factor(rsf_5$Vegetation)
rsf_5$Direction = as.factor(rsf_5$Direction)
str(rsf_5)

plyr::count(rsf_5$Vegetation)

#look at main rsf file vegetation types
#Combining several vegetation types into one category (taking those cover types that are less than 10 in frequency and adding them to a category called "Other")
levels(rsf_5$Vegetation) [levels(rsf_5$Vegetation)=="LF 100: Recently Disturbed Other - Tree"] <- "Other"
levels(rsf_5$Vegetation) [levels(rsf_5$Vegetation)=="LF 12: Snow-Ice"] <- "Other"
levels(rsf_5$Vegetation) [levels(rsf_5$Vegetation)=="LF 63: Recently Logged - Shrub"] <- "Other"
levels(rsf_5$Vegetation) [levels(rsf_5$Vegetation)=="LF 64: Recently Logged - Tree"] <- "Other"
levels(rsf_5$Vegetation) [levels(rsf_5$Vegetation)=="SAF 237: Interior Ponderosa Pine"] <- "Other"
levels(rsf_5$Vegetation) [levels(rsf_5$Vegetation)=="SAF 247: Jeffrey Pine"] <- "Other"


plyr::count(rsf_5$Vegetation)

#Add predictions column to each data frame
rsf_5$predictions = predict(m1, newdata = rsf_5, type = "response")
summary(rsf_5$predictions)

#create new df with just the coordinates and predictions
rsf_5_predict = select(rsf_5, POINT_X, POINT_Y, predictions)

#write new df to .csv
write.csv(rsf_5_predict, file = "rsf_5_predict.csv")
############################################################################





#6#
#####################################################################################################
##rsf_6##
rsf = read.csv("RSF_Ready_DistributionOnly.csv", header = T) 
str(rsf)
summary(rsf)

###putting aspect values into "bins"
rsf$Direction<-ifelse(rsf$Aspect <= 22.5, "N",
                      
                      ifelse(rsf$Aspect > 22.5 & rsf$Aspect <= 67.5, "NE",
                             
                             ifelse(rsf$Aspect > 67.5 & rsf$Aspect <= 112.5, "E",
                                    
                                    ifelse(rsf$Aspect > 112.5 & rsf$Aspect <= 157.5, "SE",
                                           
                                           ifelse(rsf$Aspect > 157.5 & rsf$Aspect <= 202.5, "S",
                                                  
                                                  ifelse(rsf$Aspect > 202.5 & rsf$Aspect <= 247.5, "SW",
                                                         
                                                         ifelse(rsf$Aspect > 247.5 & rsf$Aspect <= 292.5, "W",
                                                                
                                                                ifelse(rsf$Aspect > 292.5 & rsf$Aspect <= 337.5, "NW",
                                                                       
                                                                       ifelse(rsf$Aspect > 337.5 & rsf$Aspect <= 360, "N",
                                                                              
                                                                              ifelse(rsf$Aspect > 360 ,"N", "NA"))))))))))






#convert to factors
rsf$Use = as.factor(rsf$Use)
rsf$Vegetation = as.factor(rsf$Vegetation)
rsf$Direction = as.factor(rsf$Direction)
str(rsf)
summary(rsf)



#Rescale
rsf$scale_Curvature = scale(rsf$Curvature)
rsf$scale_RoadsProximity = scale(rsf$RoadsProximity)
rsf$scale_Elevation = scale(rsf$Elevation)
rsf$scale_Ruggedness = scale(rsf$Ruggedness)
rsf$scale_Slope = scale(rsf$Slope)


####
##Read in subsets of point data that has been broken into 10 different data frames
###6###
rsf_6 = read.csv("DEMPointsVeg_6.csv", header = TRUE)
str(rsf_6)

###putting aspect values into "bins"
rsf_6$Direction<-ifelse(rsf_6$Aspect <= 22.5, "N",
                        
                        ifelse(rsf_6$Aspect > 22.5 & rsf_6$Aspect <= 67.5, "NE",
                               
                               ifelse(rsf_6$Aspect > 67.5 & rsf_6$Aspect <= 112.5, "E",
                                      
                                      ifelse(rsf_6$Aspect > 112.5 & rsf_6$Aspect <= 157.5, "SE",
                                             
                                             ifelse(rsf_6$Aspect > 157.5 & rsf_6$Aspect <= 202.5, "S",
                                                    
                                                    ifelse(rsf_6$Aspect > 202.5 & rsf_6$Aspect <= 247.5, "SW",
                                                           
                                                           ifelse(rsf_6$Aspect > 247.5 & rsf_6$Aspect <= 292.5, "W",
                                                                  
                                                                  ifelse(rsf_6$Aspect > 292.5 & rsf_6$Aspect <= 337.5, "NW",
                                                                         
                                                                         ifelse(rsf_6$Aspect > 337.5 & rsf_6$Aspect <= 360, "N",
                                                                                
                                                                                ifelse(rsf_6$Aspect > 360 ,"N", "NA"))))))))))





#scale the variables to match headings from model
rsf_6$scale_Curvature = scale(rsf_6$Curvature)
rsf_6$scale_RoadsProximity = scale(rsf_6$EucDistRoads)
rsf_6$scale_Elevation = scale(rsf_6$Elevation)
rsf_6$scale_Ruggedness = scale(rsf_6$Ruggedness)
rsf_6$scale_Slope = scale(rsf_6$Slope)
rsf_6$Vegetation = rsf_6$SAF_SRM

rsf_6$Vegetation = as.factor(rsf_6$Vegetation)
rsf_6$Direction = as.factor(rsf_6$Direction)
str(rsf_6)


###Adding an "other" variable in the vegetation data so it can be compared to the other data frames (anything thats less than 10 points)
#RSF MAIN FILE
plyr::count(rsf$Vegetation)


#Combining several vegetation types into one category (taking those cover types that are less than 10 in frequency and adding them to a category called "Other")
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SAF 211: White Fir"] <- "Other"



plyr::count(rsf$Vegetation)


#A Priori Model to be ran on the updated main file
m1 = glm(Use~scale_RoadsProximity + scale_Curvature + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")

#RSF_#
plyr::count(rsf_6$Vegetation)

#look at main rsf file vegetation types
#Combining several vegetation types into one category (taking those cover types that are less than 10 in frequency and adding them to a category called "Other")
levels(rsf_6$Vegetation) [levels(rsf_6$Vegetation)=="LF 100: Recently Disturbed Other - Tree"] <- "Other"
levels(rsf_6$Vegetation) [levels(rsf_6$Vegetation)=="LF 63: Recently Logged - Shrub"] <- "Other"
levels(rsf_6$Vegetation) [levels(rsf_6$Vegetation)=="LF 64: Recently Logged - Tree"] <- "Other"




plyr::count(rsf_6$Vegetation)

#Add predictions column to each data frame
rsf_6$predictions = predict(m1, newdata = rsf_6, type = "response")
summary(rsf_6$predictions)

#create new df with just the coordinates and predictions
rsf_6_predict = select(rsf_6, POINT_X, POINT_Y, predictions)

#write new df to .csv
write.csv(rsf_6_predict, file = "rsf_6_predict.csv")
############################################################################





#7#
#####################################################################################################
##rsf_7##
rsf = read.csv("RSF_Ready_DistributionOnly.csv", header = T) 
str(rsf)
summary(rsf)

###putting aspect values into "bins"
rsf$Direction<-ifelse(rsf$Aspect <= 22.5, "N",
                      
                      ifelse(rsf$Aspect > 22.5 & rsf$Aspect <= 67.5, "NE",
                             
                             ifelse(rsf$Aspect > 67.5 & rsf$Aspect <= 112.5, "E",
                                    
                                    ifelse(rsf$Aspect > 112.5 & rsf$Aspect <= 157.5, "SE",
                                           
                                           ifelse(rsf$Aspect > 157.5 & rsf$Aspect <= 202.5, "S",
                                                  
                                                  ifelse(rsf$Aspect > 202.5 & rsf$Aspect <= 247.5, "SW",
                                                         
                                                         ifelse(rsf$Aspect > 247.5 & rsf$Aspect <= 292.5, "W",
                                                                
                                                                ifelse(rsf$Aspect > 292.5 & rsf$Aspect <= 337.5, "NW",
                                                                       
                                                                       ifelse(rsf$Aspect > 337.5 & rsf$Aspect <= 360, "N",
                                                                              
                                                                              ifelse(rsf$Aspect > 360 ,"N", "NA"))))))))))






#convert to factors
rsf$Use = as.factor(rsf$Use)
rsf$Vegetation = as.factor(rsf$Vegetation)
rsf$Direction = as.factor(rsf$Direction)
str(rsf)
summary(rsf)



#Rescale
rsf$scale_Curvature = scale(rsf$Curvature)
rsf$scale_RoadsProximity = scale(rsf$RoadsProximity)
rsf$scale_Elevation = scale(rsf$Elevation)
rsf$scale_Ruggedness = scale(rsf$Ruggedness)
rsf$scale_Slope = scale(rsf$Slope)


####
##Read in subsets of point data that has been broken into 10 different data frames
###7###
rsf_7 = read.csv("DEMPointsVeg_7_corrected_cleaned.csv", header = TRUE)
str(rsf_7)

###putting aspect values into "bins"
rsf_7$Direction<-ifelse(rsf_7$Aspect <= 22.5, "N",
                        
                        ifelse(rsf_7$Aspect > 22.5 & rsf_7$Aspect <= 67.5, "NE",
                               
                               ifelse(rsf_7$Aspect > 67.5 & rsf_7$Aspect <= 112.5, "E",
                                      
                                      ifelse(rsf_7$Aspect > 112.5 & rsf_7$Aspect <= 157.5, "SE",
                                             
                                             ifelse(rsf_7$Aspect > 157.5 & rsf_7$Aspect <= 202.5, "S",
                                                    
                                                    ifelse(rsf_7$Aspect > 202.5 & rsf_7$Aspect <= 247.5, "SW",
                                                           
                                                           ifelse(rsf_7$Aspect > 247.5 & rsf_7$Aspect <= 292.5, "W",
                                                                  
                                                                  ifelse(rsf_7$Aspect > 292.5 & rsf_7$Aspect <= 337.5, "NW",
                                                                         
                                                                         ifelse(rsf_7$Aspect > 337.5 & rsf_7$Aspect <= 360, "N",
                                                                                
                                                                                ifelse(rsf_7$Aspect > 360 ,"N", "NA"))))))))))





#scale the variables to match headings from model
rsf_7$scale_Curvature = scale(rsf_7$Curvature)
rsf_7$scale_RoadsProximity = scale(rsf_7$EucDistRoads)
rsf_7$scale_Elevation = scale(rsf_7$Elevation)
rsf_7$scale_Ruggedness = scale(rsf_7$Ruggedness)
rsf_7$scale_Slope = scale(rsf_7$Slope)
rsf_7$Vegetation = rsf_7$SAF_SRM

rsf_7$Vegetation = as.factor(rsf_7$Vegetation)
rsf_7$Direction = as.factor(rsf_7$Direction)
str(rsf_7)


###Adding an "other" variable in the vegetation data so it can be compared to the other data frames (anything thats less than 10 points)
#RSF MAIN FILE
plyr::count(rsf$Vegetation)


#Combining several vegetation types into one category (taking those cover types that are less than 10 in frequency and adding them to a category called "Other")
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SAF 208: Whitebark Pine"] <- "Other"
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SAF 211: White Fir"] <- "Other"
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SRM 212: Blackbush"] <- "Other"



plyr::count(rsf$Vegetation)


#A Priori Model to be ran on the updated main file
m1 = glm(Use~scale_RoadsProximity + scale_Curvature + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")

#RSF_#
plyr::count(rsf_7$Vegetation)

#look at main rsf file vegetation types
#Combining several vegetation types into one category (taking those cover types that are less than 10 in frequency and adding them to a category called "Other")
levels(rsf_7$Vegetation) [levels(rsf_7$Vegetation)=="LF 63: Recently Logged - Shrub"] <- "Other"
levels(rsf_7$Vegetation) [levels(rsf_7$Vegetation)=="LF 64: Recently Logged - Tree"] <- "Other"
levels(rsf_7$Vegetation) [levels(rsf_7$Vegetation)=="SRM 101: Bluebunch Wheatgrass"] <- "Other"




plyr::count(rsf_7$Vegetation)

#Add predictions column to each data frame
rsf_7$predictions = predict(m1, newdata = rsf_7, type = "response")
summary(rsf_7$predictions)

#create new df with just the coordinates and predictions
rsf_7_predict = select(rsf_7, POINT_X, POINT_Y, predictions)

#write new df to .csv
write.csv(rsf_7_predict, file = "rsf_7_predict.csv")
############################################################################





#8#
#####################################################################################################
##rsf_8##
rsf = read.csv("RSF_Ready_DistributionOnly.csv", header = T) 
str(rsf)
summary(rsf)

###putting aspect values into "bins"
rsf$Direction<-ifelse(rsf$Aspect <= 22.5, "N",
                      
                      ifelse(rsf$Aspect > 22.5 & rsf$Aspect <= 67.5, "NE",
                             
                             ifelse(rsf$Aspect > 67.5 & rsf$Aspect <= 112.5, "E",
                                    
                                    ifelse(rsf$Aspect > 112.5 & rsf$Aspect <= 157.5, "SE",
                                           
                                           ifelse(rsf$Aspect > 157.5 & rsf$Aspect <= 202.5, "S",
                                                  
                                                  ifelse(rsf$Aspect > 202.5 & rsf$Aspect <= 247.5, "SW",
                                                         
                                                         ifelse(rsf$Aspect > 247.5 & rsf$Aspect <= 292.5, "W",
                                                                
                                                                ifelse(rsf$Aspect > 292.5 & rsf$Aspect <= 337.5, "NW",
                                                                       
                                                                       ifelse(rsf$Aspect > 337.5 & rsf$Aspect <= 360, "N",
                                                                              
                                                                              ifelse(rsf$Aspect > 360 ,"N", "NA"))))))))))






#convert to factors
rsf$Use = as.factor(rsf$Use)
rsf$Vegetation = as.factor(rsf$Vegetation)
rsf$Direction = as.factor(rsf$Direction)
str(rsf)
summary(rsf)



#Rescale
rsf$scale_Curvature = scale(rsf$Curvature)
rsf$scale_RoadsProximity = scale(rsf$RoadsProximity)
rsf$scale_Elevation = scale(rsf$Elevation)
rsf$scale_Ruggedness = scale(rsf$Ruggedness)
rsf$scale_Slope = scale(rsf$Slope)


####
##Read in subsets of point data that has been broken into 10 different data frames
###8###
rsf_8 = read.csv("DEMPointsVeg_8_corrected_cleaned.csv", header = TRUE)
str(rsf_8)

###putting aspect values into "bins"
rsf_8$Direction<-ifelse(rsf_8$Aspect <= 22.5, "N",
                        
                        ifelse(rsf_8$Aspect > 22.5 & rsf_8$Aspect <= 67.5, "NE",
                               
                               ifelse(rsf_8$Aspect > 67.5 & rsf_8$Aspect <= 112.5, "E",
                                      
                                      ifelse(rsf_8$Aspect > 112.5 & rsf_8$Aspect <= 157.5, "SE",
                                             
                                             ifelse(rsf_8$Aspect > 157.5 & rsf_8$Aspect <= 202.5, "S",
                                                    
                                                    ifelse(rsf_8$Aspect > 202.5 & rsf_8$Aspect <= 247.5, "SW",
                                                           
                                                           ifelse(rsf_8$Aspect > 247.5 & rsf_8$Aspect <= 292.5, "W",
                                                                  
                                                                  ifelse(rsf_8$Aspect > 292.5 & rsf_8$Aspect <= 337.5, "NW",
                                                                         
                                                                         ifelse(rsf_8$Aspect > 337.5 & rsf_8$Aspect <= 360, "N",
                                                                                
                                                                                ifelse(rsf_8$Aspect > 360 ,"N", "NA"))))))))))





#scale the variables to match headings from model
rsf_8$scale_Curvature = scale(rsf_8$Curvature)
rsf_8$scale_RoadsProximity = scale(rsf_8$EucDistRoads)
rsf_8$scale_Elevation = scale(rsf_8$Elevation)
rsf_8$scale_Ruggedness = scale(rsf_8$Ruggedness)
rsf_8$scale_Slope = scale(rsf_8$Slope)
rsf_8$Vegetation = rsf_8$SAF_SRM

rsf_8$Vegetation = as.factor(rsf_8$Vegetation)
rsf_8$Direction = as.factor(rsf_8$Direction)
str(rsf_8)


###Adding an "other" variable in the vegetation data so it can be compared to the other data frames (anything thats less than 10 points)
#RSF MAIN FILE
plyr::count(rsf$Vegetation)


#Combining several vegetation types into one category (taking those cover types that are less than 10 in frequency and adding them to a category called "Other")
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SRM 107: Western Juniper-Big Sagebrush-Bluebunch Wheatgrass"] <- "Other"
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SRM 212: Blackbush"] <- "Other"




plyr::count(rsf$Vegetation)


#A Priori Model to be ran on the updated main file
m1 = glm(Use~scale_RoadsProximity + scale_Curvature + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")

#RSF_#
plyr::count(rsf_8$Vegetation)

#look at main rsf file vegetation types
#Combining several vegetation types into one category (taking those cover types that are less than 10 in frequency and adding them to a category called "Other")
levels(rsf_8$Vegetation) [levels(rsf_8$Vegetation)=="LF 100: Recently Disturbed Other - Tree"] <- "Other"
levels(rsf_8$Vegetation) [levels(rsf_8$Vegetation)=="LF 63: Recently Logged - Shrub"] <- "Other"





plyr::count(rsf_8$Vegetation)

#Add predictions column to each data frame
rsf_8$predictions = predict(m1, newdata = rsf_8, type = "response")
summary(rsf_8$predictions)

#create new df with just the coordinates and predictions
rsf_8_predict = select(rsf_8, POINT_X, POINT_Y, predictions)

#write new df to .csv
write.csv(rsf_8_predict, file = "rsf_8_predict.csv")
############################################################################





#9#
#####################################################################################################
##rsf_9##
rsf = read.csv("RSF_Ready_DistributionOnly.csv", header = T) 
str(rsf)
summary(rsf)

###putting aspect values into "bins"
rsf$Direction<-ifelse(rsf$Aspect <= 22.5, "N",
                      
                      ifelse(rsf$Aspect > 22.5 & rsf$Aspect <= 67.5, "NE",
                             
                             ifelse(rsf$Aspect > 67.5 & rsf$Aspect <= 112.5, "E",
                                    
                                    ifelse(rsf$Aspect > 112.5 & rsf$Aspect <= 157.5, "SE",
                                           
                                           ifelse(rsf$Aspect > 157.5 & rsf$Aspect <= 202.5, "S",
                                                  
                                                  ifelse(rsf$Aspect > 202.5 & rsf$Aspect <= 247.5, "SW",
                                                         
                                                         ifelse(rsf$Aspect > 247.5 & rsf$Aspect <= 292.5, "W",
                                                                
                                                                ifelse(rsf$Aspect > 292.5 & rsf$Aspect <= 337.5, "NW",
                                                                       
                                                                       ifelse(rsf$Aspect > 337.5 & rsf$Aspect <= 360, "N",
                                                                              
                                                                              ifelse(rsf$Aspect > 360 ,"N", "NA"))))))))))






#convert to factors
rsf$Use = as.factor(rsf$Use)
rsf$Vegetation = as.factor(rsf$Vegetation)
rsf$Direction = as.factor(rsf$Direction)
str(rsf)
summary(rsf)



#Rescale
rsf$scale_Curvature = scale(rsf$Curvature)
rsf$scale_RoadsProximity = scale(rsf$RoadsProximity)
rsf$scale_Elevation = scale(rsf$Elevation)
rsf$scale_Ruggedness = scale(rsf$Ruggedness)
rsf$scale_Slope = scale(rsf$Slope)


####
##Read in subsets of point data that has been broken into 10 different data frames
###9###
rsf_9 = read.csv("DEMPointsVeg_9_corrected_cleaned.csv", header = TRUE)
str(rsf_9)

###putting aspect values into "bins"
rsf_9$Direction<-ifelse(rsf_9$Aspect <= 22.5, "N",
                        
                        ifelse(rsf_9$Aspect > 22.5 & rsf_9$Aspect <= 67.5, "NE",
                               
                               ifelse(rsf_9$Aspect > 67.5 & rsf_9$Aspect <= 112.5, "E",
                                      
                                      ifelse(rsf_9$Aspect > 112.5 & rsf_9$Aspect <= 157.5, "SE",
                                             
                                             ifelse(rsf_9$Aspect > 157.5 & rsf_9$Aspect <= 202.5, "S",
                                                    
                                                    ifelse(rsf_9$Aspect > 202.5 & rsf_9$Aspect <= 247.5, "SW",
                                                           
                                                           ifelse(rsf_9$Aspect > 247.5 & rsf_9$Aspect <= 292.5, "W",
                                                                  
                                                                  ifelse(rsf_9$Aspect > 292.5 & rsf_9$Aspect <= 337.5, "NW",
                                                                         
                                                                         ifelse(rsf_9$Aspect > 337.5 & rsf_9$Aspect <= 360, "N",
                                                                                
                                                                                ifelse(rsf_9$Aspect > 360 ,"N", "NA"))))))))))





#scale the variables to match headings from model
rsf_9$scale_Curvature = scale(rsf_9$Curvature)
rsf_9$scale_RoadsProximity = scale(rsf_9$EucDistRoads)
rsf_9$scale_Elevation = scale(rsf_9$Elevation)
rsf_9$scale_Ruggedness = scale(rsf_9$Ruggedness)
rsf_9$scale_Slope = scale(rsf_9$Slope)
rsf_9$Vegetation = rsf_9$SAF_SRM

rsf_9$Vegetation = as.factor(rsf_9$Vegetation)
rsf_9$Direction = as.factor(rsf_9$Direction)
str(rsf_9)


###Adding an "other" variable in the vegetation data so it can be compared to the other data frames (anything thats less than 10 points)
#RSF MAIN FILE
plyr::count(rsf$Vegetation)


#Combining several vegetation types into one category (taking those cover types that are less than 10 in frequency and adding them to a category called "Other")
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SRM 107: Western Juniper-Big Sagebrush-Bluebunch Wheatgrass"] <- "Other"
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SRM 212: Blackbush"] <- "Other"




plyr::count(rsf$Vegetation)


#A Priori Model to be ran on the updated main file
m1 = glm(Use~scale_RoadsProximity + scale_Curvature + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")

#RSF_#
plyr::count(rsf_9$Vegetation)

#look at main rsf file vegetation types
#Combining several vegetation types into one category (taking those cover types that are less than 10 in frequency and adding them to a category called "Other")
levels(rsf_9$Vegetation) [levels(rsf_9$Vegetation)=="LF 100: Recently Disturbed Other - Tree"] <- "Other"
levels(rsf_9$Vegetation) [levels(rsf_9$Vegetation)=="LF 63: Recently Logged - Shrub"] <- "Other"
levels(rsf_9$Vegetation) [levels(rsf_9$Vegetation)=="LF 64: Recently Logged - Tree"] <- "Other"




plyr::count(rsf_9$Vegetation)

#Add predictions column to each data frame
rsf_9$predictions = predict(m1, newdata = rsf_9, type = "response")
summary(rsf_9$predictions)

#create new df with just the coordinates and predictions
rsf_9_predict = select(rsf_9, POINT_X, POINT_Y, predictions)

#write new df to .csv
write.csv(rsf_9_predict, file = "rsf_9_predict.csv")
############################################################################





#10#
#####################################################################################################
##rsf_10##
rsf = read.csv("RSF_Ready_DistributionOnly.csv", header = T) 
str(rsf)
summary(rsf)

###putting aspect values into "bins"
rsf$Direction<-ifelse(rsf$Aspect <= 22.5, "N",
                      
                      ifelse(rsf$Aspect > 22.5 & rsf$Aspect <= 67.5, "NE",
                             
                             ifelse(rsf$Aspect > 67.5 & rsf$Aspect <= 112.5, "E",
                                    
                                    ifelse(rsf$Aspect > 112.5 & rsf$Aspect <= 157.5, "SE",
                                           
                                           ifelse(rsf$Aspect > 157.5 & rsf$Aspect <= 202.5, "S",
                                                  
                                                  ifelse(rsf$Aspect > 202.5 & rsf$Aspect <= 247.5, "SW",
                                                         
                                                         ifelse(rsf$Aspect > 247.5 & rsf$Aspect <= 292.5, "W",
                                                                
                                                                ifelse(rsf$Aspect > 292.5 & rsf$Aspect <= 337.5, "NW",
                                                                       
                                                                       ifelse(rsf$Aspect > 337.5 & rsf$Aspect <= 360, "N",
                                                                              
                                                                              ifelse(rsf$Aspect > 360 ,"N", "NA"))))))))))






#convert to factors
rsf$Use = as.factor(rsf$Use)
rsf$Vegetation = as.factor(rsf$Vegetation)
rsf$Direction = as.factor(rsf$Direction)
str(rsf)
summary(rsf)



#Rescale
rsf$scale_Curvature = scale(rsf$Curvature)
rsf$scale_RoadsProximity = scale(rsf$RoadsProximity)
rsf$scale_Elevation = scale(rsf$Elevation)
rsf$scale_Ruggedness = scale(rsf$Ruggedness)
rsf$scale_Slope = scale(rsf$Slope)


####
##Read in subsets of point data that has been broken into 10 different data frames
###10###
rsf_10 = read.csv("DEMPointsVeg_10_corrected_cleaned.csv", header = TRUE)
str(rsf_10)

###putting aspect values into "bins"
rsf_10$Direction<-ifelse(rsf_10$Aspect <= 22.5, "N",
                        
                        ifelse(rsf_10$Aspect > 22.5 & rsf_10$Aspect <= 67.5, "NE",
                               
                               ifelse(rsf_10$Aspect > 67.5 & rsf_10$Aspect <= 112.5, "E",
                                      
                                      ifelse(rsf_10$Aspect > 112.5 & rsf_10$Aspect <= 157.5, "SE",
                                             
                                             ifelse(rsf_10$Aspect > 157.5 & rsf_10$Aspect <= 202.5, "S",
                                                    
                                                    ifelse(rsf_10$Aspect > 202.5 & rsf_10$Aspect <= 247.5, "SW",
                                                           
                                                           ifelse(rsf_10$Aspect > 247.5 & rsf_10$Aspect <= 292.5, "W",
                                                                  
                                                                  ifelse(rsf_10$Aspect > 292.5 & rsf_10$Aspect <= 337.5, "NW",
                                                                         
                                                                         ifelse(rsf_10$Aspect > 337.5 & rsf_10$Aspect <= 360, "N",
                                                                                
                                                                                ifelse(rsf_10$Aspect > 360 ,"N", "NA"))))))))))





#scale the variables to match headings from model
rsf_10$scale_Curvature = scale(rsf_10$Curvature)
rsf_10$scale_RoadsProximity = scale(rsf_10$EucDistRoads)
rsf_10$scale_Elevation = scale(rsf_10$Elevation)
rsf_10$scale_Ruggedness = scale(rsf_10$Ruggedness)
rsf_10$scale_Slope = scale(rsf_10$Slope)
rsf_10$Vegetation = rsf_10$SAF_SRM

rsf_10$Vegetation = as.factor(rsf_10$Vegetation)
rsf_10$Direction = as.factor(rsf_10$Direction)
str(rsf_10)


###Adding an "other" variable in the vegetation data so it can be compared to the other data frames (anything thats less than 10 points)
#RSF MAIN FILE
plyr::count(rsf$Vegetation)


#Combining several vegetation types into one category (taking those cover types that are less than 10 in frequency and adding them to a category called "Other")
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SAF 210: Interior Douglas-Fir"] <- "Other"
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SAF 211: White Fir"] <- "Other"
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SRM 107: Western Juniper-Big Sagebrush-Bluebunch Wheatgrass"] <- "Other"
levels(rsf$Vegetation) [levels(rsf$Vegetation)=="SRM 212: Blackbush"] <- "Other"




plyr::count(rsf$Vegetation)


#A Priori Model to be ran on the updated main file
m1 = glm(Use~scale_RoadsProximity + scale_Curvature + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")

#RSF_#
plyr::count(rsf_10$Vegetation)

#look at main rsf file vegetation types
#Combining several vegetation types into one category (taking those cover types that are less than 10 in frequency and adding them to a category called "Other")
levels(rsf_10$Vegetation) [levels(rsf_10$Vegetation)=="LF 63: Recently Logged - Shrub"] <- "Other"
levels(rsf_10$Vegetation) [levels(rsf_10$Vegetation)=="LF 64: Recently Logged - Tree"] <- "Other"




plyr::count(rsf_10$Vegetation)

#Add predictions column to each data frame
rsf_10$predictions = predict(m1, newdata = rsf_10, type = "response")
summary(rsf_10$predictions)

#create new df with just the coordinates and predictions
rsf_10_predict = select(rsf_10, POINT_X, POINT_Y, predictions)

#write new df to .csv
write.csv(rsf_10_predict, file = "rsf_10_predict.csv")
############################################################################