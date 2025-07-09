CXX = g++
CXXFLAGS = -std=c++11 -Wall
LIBS = -ljsoncpp

TARGET = client
SRC = client.cpp

all: $(TARGET)

$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRC) $(LIBS)

clean:
	rm -f $(TARGET)
