## Read data
my_file = read.csv("C:/Users/baseb/Desktop/CSE 6242/Project/qdata.csv")
colnames(my_file)
mydata = my_file[,1:18]
head(mydata)

## The tourist attractions suggested by these apps are attractive
# APP vs Google
wilcox.test(mydata[,1], mydata[,3])
# APP vs Tripadvisor
wilcox.test(mydata[,2], mydata[,3])

##The tourist attractions suggested by these apps are easy to get to. # APP vs Google
wilcox.test(mydata[,4], mydata[,6])
# APP vs Tripadvisor
wilcox.test(mydata[,5], mydata[,6])

##Overall speaking, I am satisfied with the tourist spots recommended by these apps.
# APP vs Google
wilcox.test(mydata[,7], mydata[,9])
# APP vs Tripadvisor
wilcox.test(mydata[,8], mydata[,9])

##The apps' user interfaces are intuitive. 
# APP vs Google
wilcox.test(mydata[,10], mydata[,12])
# APP vs Tripadvisor
wilcox.test(mydata[,11], mydata[,12])

##It is easy to create an itinerary using the apps.
# APP vs Google
wilcox.test(mydata[,13], mydata[,15])
# APP vs Tripadvisor
wilcox.test(mydata[,14], mydata[,15])

##Overall speaking, I am satisfied with the apps' user interfaces.
# APP vs Google
wilcox.test(mydata[,17], mydata[,18])
# APP vs Tripadvisor
wilcox.test(mydata[,16], mydata[,18])

